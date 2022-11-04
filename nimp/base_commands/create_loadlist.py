# -*- coding: utf-8 -*-
# Copyright (c) 2014-2022 Dontnod Entertainment

# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:

# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
import argparse
import json
import os
import re

import nimp.command
import nimp.utils.p4


class CreateLoadlist(nimp.command.Command):
	''' Generates a list of modified files from a set of Perforce changelists '''

	def configure_arguments(self, env, parser):
		parser.add_argument('changelists', nargs = argparse.ZERO_OR_MORE, help = 'select the changelists to list files from. Defaults to listing all files in havelist', default=[])
		parser.add_argument('-o', '--output', help = 'output file')
		parser.add_argument('-d', '--in-dirs', nargs=argparse.ZERO_OR_MORE, default=['//{p4client}/...'], help='Specify workspace root paths to search from')
		parser.add_argument('-e', '--extensions', nargs = argparse.ZERO_OR_MORE, help = 'file extensions to include', default = [ 'uasset', 'umap' ])
		parser.add_argument('--check-empty', action = 'store_true', help = 'Returns check empty in json format')
		parser.add_argument('--clean', action='store_true', help='Loadlist cleanup')
		nimp.utils.p4.add_arguments(parser)
		nimp.command.add_common_arguments(parser, 'dry_run', 'slice_job')
		return True

	def is_available(self, env):
		return env.is_unreal, ''

	def get_modified_files(self, env, extensions):
		p4 = nimp.utils.p4.get_client(env)

		# Do not use '//...' which will also list files not mapped to workspace
		paths = [env.format(e) for e in env.in_dirs]

		changelists = [f'@{cl}' for cl in env.changelists]
		if len(changelists) <= 0:
			changelists = ['#have']

		if len(extensions) <= 0:
			extensions = ['']

		filespecs = []
		for path in paths:
			for ext in extensions:
				for cl in changelists:
					filespecs.append(f"{path}{ext}{cl}")

		base_command = [
			"fstat",
			# Only list modified files currently accessible
			"-F", "^headAction=delete & ^headAction=move/delete"
		]

		modified_files = set()
		for (filepath, ) in p4._parse_command_output(base_command + filespecs, r"^\.\.\. clientFile(.*)$", hide_output=True):
			modified_files.add(os.path.normpath(filepath))

		# Needed for sorting and ease debug
		modified_files = list(modified_files)
		modified_files.sort()

		if env.slice_job_count is not None and env.slice_job_count > 1:
			# slice modified files
			# use a simple heuristic to spread the load between slices
			# as demanding files tends to be in the same directory
			slice = []
			for idx, elem in enumerate(modified_files):
				if (idx % env.slice_job_count) == (env.slice_job_index - 1):
					slice.append(elem)

			modified_files = slice

		return modified_files

	def run(self, env):
		loadlist_path = self.setup_loadlist_path(env)
		if env.clean:
			nimp.system.try_remove(loadlist_path, dry_run=env.dry_run)
		loadlist_files = self.get_modified_files(env, env.extensions)
		if env.check_empty:
			return self.check_empty_loadlist(loadlist_files)
		self.write_and_display_loadlist(env, loadlist_path, loadlist_files)

		return True

	def setup_loadlist_path(self, env):
		loadlist_path = env.output if env.output else f'{env.unreal_loadlist}'
		loadlist_path = os.path.abspath(env.format(nimp.system.sanitize_path(loadlist_path)))
		return loadlist_path

	def write_and_display_loadlist(self, env, loadlist_path, modified_files):
		if not env.dry_run:
			with open(loadlist_path, 'w') as output:
				for file in modified_files:
					print(file)
					output.write(f'{file}\n')

	def check_empty_loadlist(self, modified_files):
		results = {'loadlist_is_empty': True}
		if modified_files:
			results['loadlist_is_empty'] = False

		json_content = json.dumps(results, indent=4)
		print('<loadlist_start>')
		print(json_content)
		print('<loadlist_end>')
		return True
