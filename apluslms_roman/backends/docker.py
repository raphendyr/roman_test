import docker
from os.path import join

from ..helpers import cached_property
from . import Backend


Mount = docker.types.Mount


class DockerBackend(Backend):
    @cached_property
    def _client(self):
        return docker.from_env()

    def _run_opts(self, step):
        env = self.environment

        opts = dict(
            image=step.img,
            command=step.cmd,
            environment=step.env,
            user='{}:{}'.format(env.uid, env.gid),
        )

        # mounts and workdir
        if step.mnt:
            opts['mounts'] = [Mount(step.mnt, env.course_path, type='bind', read_only=False)]
            opts['working_dir'] = step.mnt
        else:
            wpath = self.WORK_PATH
            opts['mounts'] = [
                Mount(wpath, None, type='tmpfs', read_only=False, tmpfs_size=self.WORK_SIZE),
                Mount(join(wpath, 'src'), env.course_path, type='bind', read_only=True),
                Mount(join(wpath, 'build'), join(env.course_path, '_build'), type='bind', read_only=False),
            ]
            opts['working_dir'] = wpath

        return opts

    def prepare(self, steps, out):
        client = self._client
        for i, step in enumerate(steps):
            image, tag = step.img.split(':', 1)
            try:
                img = client.images.get(step.img)
            except docker.errors.ImageNotFound:
                out.manager(i, "Downloading image {}".format(step.img))
                img = client.images.pull(image, tag)

    def build(self, steps, out):
        client = self._client
        for i, step in enumerate(steps):
            opts = self._run_opts(step)
            out.manager(i, "Running container {}:".format(opts['image']))
            container = client.containers.create(**opts)

            try:
                container.start()

                for line in container.logs(stderr=True, stream=True):
                    out.container(i, line.decode('utf-8'))
            finally:
                container.remove()
