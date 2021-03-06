#!/usr/bin/env python
# Copyright 2016 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
################################################################################

from __future__ import print_function
import argparse
import errno
import os
import pipes
import re
import shutil
import string
import subprocess
import sys
import tempfile
import templates
import time

OSSFUZZ_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
BUILD_DIR = os.path.join(OSSFUZZ_DIR, 'build')


def main():
  os.chdir(OSSFUZZ_DIR)
  if not os.path.exists(BUILD_DIR):
    os.mkdir(BUILD_DIR)

  parser = argparse.ArgumentParser('helper.py', description='oss-fuzz helpers')
  subparsers = parser.add_subparsers(dest='command')

  generate_parser = subparsers.add_parser(
      'generate', help='Generate files for new project.')
  generate_parser.add_argument('project_name')

  build_image_parser = subparsers.add_parser(
      'build_image', help='Build an image.')
  build_image_parser.add_argument('project_name')

  build_fuzzers_parser = subparsers.add_parser(
      'build_fuzzers', help='Build fuzzers for a project.')
  _add_engine_args(build_fuzzers_parser)
  _add_sanitizer_args(build_fuzzers_parser)
  _add_commit_args(build_fuzzers_parser)
  _add_environment_args(build_fuzzers_parser)
  build_fuzzers_parser.add_argument('-d', '--detached', action='store_true', help='run container in detached mode') 
  build_fuzzers_parser.add_argument('-f', '--fuzzer_name', help='name of the fuzzer')
  build_fuzzers_parser.add_argument('project_name')
  build_fuzzers_parser.add_argument('source_path', help='path of local source',
                      nargs='?')

  run_fuzzer_parser = subparsers.add_parser(
      'run_fuzzer', help='Run a fuzzer.')
  _add_engine_args(run_fuzzer_parser)
  _add_commit_args(run_fuzzer_parser)
  run_fuzzer_parser.add_argument('project_name', help='name of the project')
  run_fuzzer_parser.add_argument('fuzzer_name', help='name of the fuzzer')
  run_fuzzer_parser.add_argument('fuzzer_args', help='arguments to pass to the fuzzer',
                      nargs=argparse.REMAINDER)

  coverage_parser = subparsers.add_parser(
      'coverage', help='Run a fuzzer for a while and generate coverage.')
  _add_commit_args(coverage_parser)
  coverage_parser.add_argument('--run_time', default=60,
                      help='time in seconds to run fuzzer')
  coverage_parser.add_argument('project_name', help='name of the project')
  coverage_parser.add_argument('fuzzer_name', help='name of the fuzzer')
  coverage_parser.add_argument('fuzzer_args', help='arguments to pass to the fuzzer',
                      nargs=argparse.REMAINDER)

  reproduce_parser = subparsers.add_parser(
      'reproduce', help='Reproduce a crash.')
  _add_commit_args(reproduce_parser)
  reproduce_parser.add_argument('project_name', help='name of the project')
  reproduce_parser.add_argument('fuzzer_name', help='name of the fuzzer')
  reproduce_parser.add_argument('testcase_path', help='path of local testcase')
  reproduce_parser.add_argument('fuzzer_args', help='arguments to pass to the fuzzer',
                      nargs=argparse.REMAINDER)

  shell_parser = subparsers.add_parser(
      'shell', help='Run /bin/bash in an image.')
  _add_commit_args(shell_parser)
  shell_parser.add_argument('project_name', help='name of the project')
  shell_parser.add_argument('-f', '--fuzzer_name', help='name of the fuzzer')
  _add_engine_args(shell_parser)
  _add_sanitizer_args(shell_parser)
  _add_environment_args(shell_parser)

  args = parser.parse_args()
  if args.command == 'generate':
    return generate(args)
  elif args.command == 'build_image':
    return build_image(args)
  elif args.command == 'build_fuzzers':
    return build_fuzzers(args)
  elif args.command == 'run_fuzzer':
    return run_fuzzer(args)
  elif args.command == 'coverage':
    return coverage(args)
  elif args.command == 'reproduce':
    return reproduce(args)
  elif args.command == 'shell':
    return shell(args)

  return 0


def _is_base_image(image_name):
  """Checks if the image name is a base image."""
  return os.path.exists(os.path.join('infra', 'base-images', image_name))


def _check_project_exists(project_name):
  """Checks if a project exists."""
  if not os.path.exists(os.path.join(OSSFUZZ_DIR, 'projects', project_name)):
    print(project_name, 'does not exist', file=sys.stderr)
    return False

  return True


def _check_fuzzer_exists(project_name, commit, fuzzer_name):
  """Checks if a fuzzer exists."""
  command = ['docker', 'run', '--rm']
  command.extend(['-v', '%s/%s:/out' % (os.path.join(BUILD_DIR, 'out', project_name),
			    	        commit)])
  command.append('ubuntu:16.04')

  command.extend(['/bin/bash', '-c', 'test -f /out/%s' % fuzzer_name])

  try:
    subprocess.check_call(command)
  except subprocess.CalledProcessError:
    print(fuzzer_name,
          'does not seem to exist. Please run build_fuzzers first.',
          file=sys.stderr)
    return False

  return True


def _get_absolute_path(path):
  """Returns absolute path with user expansion."""
  return os.path.abspath(os.path.expanduser(path))


def _get_command_string(command):
  """Returns a shell escaped command string."""
  return ' '.join(pipes.quote(part) for part in command)


def _add_engine_args(parser):
  """Add common engine args."""
  parser.add_argument('--engine', default='aflgo',
                      choices=['libfuzzer', 'afl', 'aflgo'])


def _add_sanitizer_args(parser):
  """Add common sanitizer args."""
  parser.add_argument('--sanitizer', default='address',
                      choices=['address', 'memory', 'undefined'])


def _add_commit_args(parser):
  """Add optional commit args."""
  parser.add_argument('-c', '--commit', default='master', help="Checkout a specific commit")


def _add_environment_args(parser):
  """Add common environment args."""
  parser.add_argument('-e', action='append',
                      help="set environment variable e.g. VAR=value")


def _build_image(image_name, no_cache=False):
  """Build image."""

  is_base_image = _is_base_image(image_name)
  if is_base_image:
    image_project = 'oss-fuzz-base'
    dockerfile_dir = os.path.join('infra', 'base-images', image_name)
  else:
    image_project = 'oss-fuzz'
    if not _check_project_exists(image_name):
      return False

    dockerfile_dir = os.path.join('projects', image_name)

  build_args = []
  if no_cache:
    build_args.append('--no-cache')

  build_args += ['-t', 'gcr.io/%s/%s' % (image_project, image_name), dockerfile_dir]

  return docker_build(build_args, pull=(is_base_image and
                                        not no_cache))


def docker_run(run_args, print_output=True):
  """Call `docker run`."""
  command = ['docker', 'run', '--rm', '-i', '--cap-add', 'SYS_PTRACE']
  command.extend(run_args)

  print('Running:', _get_command_string(command))
  stdout = None
  if not print_output:
    stdout = open(os.devnull, 'w')

  try:
    subprocess.check_call(command, stdout=stdout, stderr=subprocess.STDOUT)
  except subprocess.CalledProcessError:
    return False

  return True


def docker_build(build_args, pull=False):
  """Call `docker build`."""
  command = ['docker', 'build']
  if pull:
    command.append('--pull')

  command.extend(build_args)
  print('Running:', _get_command_string(command))

  try:
    subprocess.check_call(command)
  except subprocess.CalledProcessError:
    print('docker build failed.', file=sys.stderr)
    return False

  return True


def build_image(args):
  """Build docker image."""
  # If build_image is called explicitly, don't use cache.
  if _build_image(args.project_name, no_cache=True):
    return 0

  return 1


def build_fuzzers(args):
  """Build fuzzers."""
  project_name = args.project_name

  if not args.detached and not _build_image(args.project_name):
    return 1

  env = [
      'BUILD_UID=%d' % os.getuid(),
      'FUZZING_ENGINE=' + args.engine,
      'SANITIZER=' + args.sanitizer,
      'PROJECT=' + args.project_name,
      'COMMIT=' + args.commit,
      'FUZZER=' + (args.fuzzer_name if args.fuzzer_name is not None else "")
  ]

  if args.e:
    env += args.e

  command = (
      ['docker', 'run', '--rm', '-i', '--cap-add', 'SYS_PTRACE'] +
      sum([['-e', v] for v in env], [])
  )

  if args.source_path:
    command += [
        '-v',
        '%s:/src/%s' % (_get_absolute_path(args.source_path), args.project_name)
    ]

  if args.detached:
    command += [
        '-d' 
    ]

  if args.commit is not 'master':
    command += [
         '--name', args.commit
    ]

  command += [
      '-v', '%s/%s:/out' % (os.path.join(BUILD_DIR, 'out', project_name),
			    args.commit), 
      '-v', '%s/%s:/work' % (os.path.join(BUILD_DIR, 'work', project_name),
			     args.commit),
      '-t', 'gcr.io/oss-fuzz/%s' % project_name,
      'compile'
  ]

  print('Running:', _get_command_string(command))

  try:
    subprocess.check_call(command)
  except subprocess.CalledProcessError:
    print('fuzzers build failed.', file=sys.stderr)
    return 1

  return 0


def run_fuzzer(args):
  """Runs a fuzzer in the container."""
  if not _check_project_exists(args.project_name):
    return 1

  if not _check_fuzzer_exists(args.project_name, args.commit, args.fuzzer_name):
    return 1

  if not _build_image('base-runner'):
    return 1

  env = ['FUZZING_ENGINE=' + args.engine]

  run_args = sum([['-e', v] for v in env], []) + [
      '-v', '%s/%s:/out' % (os.path.join(BUILD_DIR, 'out', args.project_name),
			    args.commit),
      '-t', 'gcr.io/oss-fuzz-base/base-runner',
      'run_fuzzer',
      args.fuzzer_name,
  ] + args.fuzzer_args

  docker_run(run_args)


def coverage(args):
  """Runs a fuzzer in the container."""
  if not _check_project_exists(args.project_name):
    return 1

  if not _check_fuzzer_exists(args.project_name, args.commit, args.fuzzer_name):
    return 1

  if not _build_image('base-runner'):
    return 1

  temp_dir = tempfile.mkdtemp()

  run_args = [
      '-v', '%s/%s:/out' % (os.path.join(BUILD_DIR, 'out', args.project_name),
			    args.commit),
      '-v', '%s:/cov' % temp_dir,
      '-w', '/cov',
      '-t', 'gcr.io/oss-fuzz-base/base-runner',
      '/out/%s' % args.fuzzer_name,
      '-dump_coverage=1',
      '-max_total_time=%s' % args.run_time
  ] + args.fuzzer_args

  print('This may take a while (running your fuzzer for %d seconds)...' %
        args.run_time)
  docker_run(run_args, print_output=False)

  run_args = [
      '-v', '%s/%s:/out' % (os.path.join(BUILD_DIR, 'out', args.project_name),
			    args.commit),
      '-v', '%s:/cov' % temp_dir,
      '-w', '/cov',
      '-p', '8001:8001',
      '-t', 'gcr.io/oss-fuzz/%s' % args.project_name,
      'coverage_report', '/out/%s' % args.fuzzer_name,
  ]

  docker_run(run_args)


def reproduce(args):
  """Reproduces a testcase in the container."""
  if not _check_project_exists(args.project_name):
    return 1

  if not _check_fuzzer_exists(args.project_name, args.commit, args.fuzzer_name):
    return 1

  if not _build_image('base-runner'):
    return 1

  run_args = [
      '-v', '%s/%s:/out' % (os.path.join(BUILD_DIR, 'out', args.project_name),
			    args.commit),
      '-v', '%s:/testcase' % _get_absolute_path(args.testcase_path),
      '-t', 'gcr.io/oss-fuzz-base/base-runner',
      'reproduce',
      args.fuzzer_name,
      '-runs=100',
  ] + args.fuzzer_args

  docker_run(run_args)


def generate(args):
  """Generate empty project files."""
  dir = os.path.join('projects', args.project_name)

  try:
    os.mkdir(dir)
  except OSError as e:
    if e.errno != errno.EEXIST:
      raise
    print(dir, 'already exists.', file=sys.stderr)
    return 1

  print('Writing new files to', dir)

  template_args = {
    'project_name' : args.project_name
  }
  with open(os.path.join(dir, 'project.yaml'), 'w') as f:
    f.write(templates.PROJECT_YAML_TEMPLATE % template_args)

  with open(os.path.join(dir, 'Dockerfile'), 'w') as f:
    f.write(templates.DOCKER_TEMPLATE % template_args)

  build_sh_path = os.path.join(dir, 'build.sh')
  with open(build_sh_path, 'w') as f:
    f.write(templates.BUILD_TEMPLATE % template_args)

  os.chmod(build_sh_path, 0o755)
  return 0


def shell(args):
  """Runs a shell within a docker image."""
  if not _build_image(args.project_name):
    return 1

  env = [
      'FUZZING_ENGINE=' + args.engine,
      'SANITIZER=' + args.sanitizer,
      'PROJECT=' + args.project_name,
      'COMMIT=' + args.commit,
      'FUZZER=' + (args.fuzzer_name if args.fuzzer_name is not None else "")
  ]

  if args.e:
    env += args.e

  run_args = sum([['-e', v] for v in env], []) + [
      '-v', '%s/%s:/out' % (os.path.join(BUILD_DIR, 'out', args.project_name),
			    args.commit),
      '-v', '%s/%s:/work' % (os.path.join(BUILD_DIR, 'work', args.project_name),
			     args.commit),
      '-t', 'gcr.io/oss-fuzz/%s' % args.project_name,
      '/bin/bash'
  ]

  docker_run(run_args)


if __name__ == '__main__':
  sys.exit(main())
