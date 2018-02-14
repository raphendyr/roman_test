import docker
from os.path import join

from ..helpers import cached_property
from . import (
    Backend,
    BuildResult,
)


Mount = docker.types.Mount


class DockerBackend(Backend):
    @cached_property
    def _client(self):
        return docker.from_env()

    def _run_opts(self, task, step):
        env = self.environment

        opts = dict(
            image=step.img,
            command=step.cmd,
            environment=step.env,
            user='{}:{}'.format(env.uid, env.gid),
        )

        # mounts and workdir
        if step.mnt:
            opts['mounts'] = [Mount(step.mnt, task.path, type='bind', read_only=False)]
            opts['working_dir'] = step.mnt
        else:
            wpath = self.WORK_PATH
            opts['mounts'] = [
                Mount(wpath, None, type='tmpfs', read_only=False, tmpfs_size=self.WORK_SIZE),
                Mount(join(wpath, 'src'), task.path, type='bind', read_only=True),
                Mount(join(wpath, 'build'), join(task.path, '_build'), type='bind', read_only=False),
            ]
            opts['working_dir'] = wpath

        return opts

    def prepare(self, task, observer):
        client = self._client
        for i, step in enumerate(task.steps):
            observer.start_step(i)
            image, tag = step.img.split(':', 1)
            try:
                img = client.images.get(step.img)
            except docker.errors.ImageNotFound:
                observer.manager_msg(i, "Downloading image {}".format(step.img))
                img = client.images.pull(image, tag)
            finally:
                observer.end_step(i)

    def build(self, task, observer):
        client = self._client
        for i, step in enumerate(task.steps):
            observer.start_step(i)
            opts = self._run_opts(task, step)
            observer.manager_msg(i, "Running container {}:".format(opts['image']))
            container = client.containers.create(**opts)

            try:
                container.start()

                for line in container.logs(stderr=True, stream=True):
                    observer.container_msg(i, line.decode('utf-8'))

                ret = container.wait(timeout=10)
                code = ret.get('StatusCode', None)
                error = ret.get('Error', None)

                if code or error:
                    return BuildResult(code, error, i)
            finally:
                container.remove()
                observer.end_step(i)
        return BuildResult()

    def verify(self):
        try:
            client = self._client
            client.ping()
        except Exception as e:
            return "{}: {}".format(e.__class__.__name__, e)

    def version_info(self):
        version = self._client.version()
        if not version:
            return

        out = []
        okeys = ['Version', 'ApiVersion', 'MinAPIVersion', 'GoVersion', 'BuildTime', 'GitCommit', 'Experimental', 'Os', 'Arch', 'KernelVersion']
        version['Name'] = 'Client'
        components = version.pop('Components', [])
        components.insert(0, version)

        for component in components:
            name = component.pop('Name', '-')
            if 'Details' in component:
                component.update(component.pop('Details'))
            out.append("Docker {}:".format(name))
            keys = okeys + [k for k in component.keys() if k not in okeys]
            for key in keys:
                if key in component:
                    val = component[key]
                    if isinstance(val, dict):
                        out.append("  {}:".format(key))
                        for k, v in val.items(): out.append("    {}: {}".format(k, v))
                    elif isinstance(val, list):
                        out.append("  {}:".format(key))
                        for v in val: out.append("   - {}".format(v))
                    else:
                        out.append("  {}: {}".format(key, val))

        return '\n'.join(out)
