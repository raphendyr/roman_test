import argparse
from os import getcwd
from os.path import abspath, expanduser, expandvars

from . import CourseConfig, Builder


def main():
    parser = argparse.ArgumentParser(description='Course material builder')
    parser.add_argument('course', nargs='?',
                        help='Location of the course definition. (default: current working dir)')

    args = parser.parse_args()

    # Resolve home, vars and relative elements from the course path
    course = args.course
    if course:
        course = abspath(expanduser(expandvars(course)))
    else:
        # default to current dir
        course = getcwd()

    config = CourseConfig.find_from(course)
    builder = Builder(config)
    builder.build()


if __name__ == '__main__':
    main()
