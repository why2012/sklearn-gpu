from distutils.extension import Extension
from Cython.Distutils import build_ext
import  os
from os.path import join as pjoin

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
		self.src_extensions.append('.cu')
		super = self.compile

		def compile(obj, sources, output_dir=None, macros=None, include_dirs=None, debug=0, extra_preargs=None, extra_postargs=None, depends=None):
			postargs = extra_postargs['cc']
			super(obj, sources, output_dir, macros, include_dirs, debug, extra_preargs, extra_postargs, depends)

		self.compile = compile

	# run the customize_compiler
	class custom_build_ext(build_ext):
		def build_extensions(self):
			customize_compiler_for_nvcc_win(self.compiler)
			build_ext.build_extensions(self)

	CUDA = locate_cuda()

	return CUDA, custom_build_ext