from distutils.extension import Extension
from Cython.Distutils import build_ext
import  os
from os.path import join as pjoin
from distutils.errors import DistutilsExecError, DistutilsPlatformError, \
							 CompileError, LibError, LinkError
from distutils.ccompiler import gen_lib_options
from distutils import log

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
					args.append("-o=" + obj)
					# suppress annoying unicode warnings
					args.extend(["-Xcompiler", "/wd 4819"])
					args.extend([_arg for _arg in pp_opts if _arg.startswith('-I')])
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
					# print('-----', args)
					self.spawn(args)
				except DistutilsExecError as msg:
					print("-----", args)
					raise CompileError(msg)

			return objects

		self.compile = compile

	def customize_linker_for_nvcc_win(self):
		def link(
			 target_desc,
			 objects,
			 output_filename,
			 output_dir=None,
			 libraries=None,
			 library_dirs=None,
			 runtime_library_dirs=None,
			 export_symbols=None,
			 debug=0,
			 extra_preargs=None,
			 extra_postargs=None,
			 build_temp=None,
			 target_lang=None):

			if not self.initialized:
				self.initialize()
			objects, output_dir = self._fix_object_args(objects, output_dir)
			fixed_args = self._fix_lib_args(libraries, library_dirs,
											runtime_library_dirs)
			libraries, library_dirs, runtime_library_dirs = fixed_args

			if runtime_library_dirs:
				self.warn("I don't know what to do with 'runtime_library_dirs': "
						   + str(runtime_library_dirs))

			lib_opts = gen_lib_options(self,
									   library_dirs, runtime_library_dirs,
									   libraries)
			if output_dir is not None:
				output_filename = os.path.join(output_dir, output_filename)

			if self._need_link(objects, output_filename):
				ldflags = self._ldflags[target_desc, debug]

				export_opts = ["/EXPORT:" + sym for sym in (export_symbols or [])]

				ld_args = (ldflags + lib_opts + export_opts +
						   objects + ['/OUT:' + output_filename])

				# The MSVC linker generates .lib and .exp files, which cannot be
				# suppressed by any linker switches. The .lib files may even be
				# needed! Make sure they are generated in the temporary build
				# directory. Since they have different names for debug and release
				# builds, they can go into the same directory.
				build_temp = os.path.dirname(objects[0])
				if export_symbols is not None:
					(dll_name, dll_ext) = os.path.splitext(
						os.path.basename(output_filename))
					implib_file = os.path.join(
						build_temp,
						self.library_filename(dll_name))
					ld_args.append ('/IMPLIB:' + implib_file)

				if extra_preargs:
					ld_args[:0] = extra_preargs
				if extra_postargs:
					ld_args.extend(extra_postargs)

				output_dir = os.path.dirname(os.path.abspath(output_filename))
				self.mkpath(output_dir)
				try:
					ld_args.append("/NODEFAULTLIB:LIBCMT")
					# print('-----', ld_args)
					log.debug('Executing "%s" %s', self.linker, ' '.join(ld_args))
					self.spawn([self.linker] + ld_args)
					self._copy_vcruntime(output_dir)
				except DistutilsExecError as msg:
					raise LinkError(msg)
			else:
				log.debug("skipping %s (up-to-date)", output_filename)

		self.link = link

	# run the customize_compiler
	class custom_build_ext(build_ext):
		def build_extensions(self):
			customize_compiler_for_nvcc_win(self.compiler)
			customize_linker_for_nvcc_win(self.compiler)
			build_ext.build_extensions(self)

	CUDA = locate_cuda()

	return CUDA, custom_build_ext