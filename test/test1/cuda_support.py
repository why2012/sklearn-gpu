from distutils.extension import Extension
from Cython.Distutils import build_ext
import  os
from os.path import join as pjoin
from distutils.errors import CompileError, DistutilsExecError

def get_cuda_support():
	def find_in_path(name, path):
		"Find a file in a search path"
		for dir in path.split(os.pathsep):
			binpath = pjoin(dir, name)
			if os.path.exists(binpath):
				return os.path.abspath(binpath)
		return None

	def locate_cuda():
		if 'CUDA_PATH' in os.environ:
			home = os.environ['CUDA_PATH']
			nvcc = pjoin(home, 'bin', 'nvcc')
		else:
			nvcc = find_in_path('nvcc', os.environ['PATH'])
			if nvcc is None:
				raise EnvironmentError('The nvcc binary could not be '
					'located in your $PATH. Either add it to your path, or set $CUDA_PATH')
			home = os.path.dirname(os.path.dirname(nvcc))

		cudaconfig = {'home':home, 'nvcc':nvcc,
					  'include': pjoin(home, 'include'),
					  'lib64': pjoin(home, 'lib', 'x64')}
		for k, v in cudaconfig.items():
			if not os.path.exists(v) and not os.path.exists(v + ".exe"):
				raise EnvironmentError('The CUDA %s path could not be located in %s' % (k, v))

		return cudaconfig

	def customize_compiler_for_nvcc_unix(self):
		self.src_extensions.append('.cu')
		# save references to the default compiler_so and _comple methods
		default_compiler_so = self.compiler_so
		super = self._compile

		def _compile(obj, src, ext, cc_args, extra_postargs, pp_opts):
			if os.path.splitext(src)[1] == '.cu':
				self.set_executable('compiler_so', CUDA['nvcc'])
				postargs = extra_postargs['nvcc']
			else:
				postargs = extra_postargs['cc']

			super(obj, src, ext, cc_args, postargs, pp_opts)
			# reset the default compiler_so, which we might have changed for cuda
			self.compiler_so = default_compiler_so

		# inject our redefined _compile method into the class
		self._compile = _compile

	def customize_compiler_for_nvcc_win(self):
		self._cuda_extensions = ['.cu']
		self.src_extensions += self._cuda_extensions
		def compile(sources,
				output_dir=None, macros=None, include_dirs=None, debug=0,
				extra_preargs=None, extra_postargs=None, depends=None):

			if not self.initialized:
				self.initialize()

			compile_info = self._setup_compile(output_dir, macros, include_dirs,
											   sources, depends, extra_postargs)
			macros, objects, extra_postargs, pp_opts, build = compile_info

			compile_opts = extra_preargs or []
			compile_opts.append('/c')
			if debug:
				compile_opts.extend(self.compile_options_debug)
			else:
				compile_opts.extend(self.compile_options)


			add_cpp_opts = False

			for obj in objects:
				try:
					src, ext = build[obj]
				except KeyError:
					continue
				if debug:
					# pass the full pathname to MSVC in debug mode,
					# this allows the debugger to find the source file
					# without asking the user to browse for it
					src = os.path.abspath(src)

				if ext in self._c_extensions:
					input_opt = "/Tc" + src
				elif ext in self._cpp_extensions:
					input_opt = "/Tp" + src
					add_cpp_opts = True
				elif ext in self._rc_extensions:
					# compile .RC to .RES file
					input_opt = src
					output_opt = "/fo" + obj
					try:
						self.spawn([self.rc] + pp_opts + [output_opt, input_opt])
					except DistutilsExecError as msg:
						raise CompileError(msg)
					continue
				elif ext in self._mc_extensions:
					# Compile .MC to .RC file to .RES file.
					#   * '-h dir' specifies the directory for the
					#	 generated include file
					#   * '-r dir' specifies the target directory of the
					#	 generated RC file and the binary message resource
					#	 it includes
					#
					# For now (since there are no options to change this),
					# we use the source-directory for the include file and
					# the build directory for the RC file and message
					# resources. This works at least for win32all.
					h_dir = os.path.dirname(src)
					rc_dir = os.path.dirname(obj)
					try:
						# first compile .MC to .RC and .H file
						self.spawn([self.mc, '-h', h_dir, '-r', rc_dir, src])
						base, _ = os.path.splitext(os.path.basename (src))
						rc_file = os.path.join(rc_dir, base + '.rc')
						# then compile .RC to .RES file
						self.spawn([self.rc, "/fo" + obj, rc_file])

					except DistutilsExecError as msg:
						raise CompileError(msg)
					continue
				elif ext in self._cuda_extensions:
					input_opt = src
				else:
					# how to handle this file?
					raise CompileError("Don't know how to compile {} to {}, ext {}"
									   .format(src, obj, ext))

				# for cuda compiler
				if ext in self._cuda_extensions:
					args = [CUDA['nvcc']]
					args.append(input_opt)
					if isinstance(extra_postargs, dict):
						args.extend(extra_postargs["nvcc"])
					else:
						args.extend(extra_postargs)
				else:
					args = [self.cc] + compile_opts + pp_opts
					if add_cpp_opts:
						args.append('/EHsc')
					args.append(input_opt)
					args.append("/Fo" + obj)
					if isinstance(extra_postargs, dict):
						args.extend(extra_postargs["cc"])
					else:
						args.extend(extra_postargs)

				try:
					self.spawn(args)
				except DistutilsExecError as msg:
					print("-----", args)
					raise CompileError(msg)

			return objects

		self.compile = compile

	# run the customize_compiler
	class custom_build_ext(build_ext):
		def build_extensions(self):
			customize_compiler_for_nvcc_win(self.compiler)
			build_ext.build_extensions(self)

	CUDA = locate_cuda()

	return CUDA, custom_build_ext