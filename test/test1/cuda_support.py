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
	    """Locate the CUDA environment on the system
	    Returns a dict with keys 'home', 'nvcc', 'include', and 'lib64'
	    and values giving the absolute path to each directory.
	    Starts by looking for the CUDA_PATH env variable. If not found, everything
	    is based on finding 'nvcc' in the PATH.
	    """

	    # first check if the CUDA_PATH env variable is in use
	    if 'CUDA_PATH' in os.environ:
	        home = os.environ['CUDA_PATH']
	        nvcc = pjoin(home, 'bin', 'nvcc')
	    else:
	        # otherwise, search the PATH for NVCC
	        nvcc = find_in_path('nvcc', os.environ['PATH'])
	        if nvcc is None:
	            raise EnvironmentError('The nvcc binary could not be '
	                'located in your $PATH. Either add it to your path, or set $CUDA_PATH')
	        home = os.path.dirname(os.path.dirname(nvcc))

	    cudaconfig = {'home':home, 'nvcc':nvcc,
	                  'include': pjoin(home, 'include'),
	                  'lib64': pjoin(home, 'lib', 'x64')}
	    for k, v in cudaconfig.items():
	        if not os.path.exists(v):
	            raise EnvironmentError('The CUDA %s path could not be located in %s' % (k, v))

	    return cudaconfig

	def customize_compiler_for_nvcc(self):
	    """inject deep into distutils to customize how the dispatch
	    to gcc/nvcc works.
	    If you subclass UnixCCompiler, it's not trivial to get your subclass
	    injected in, and still have the right customizations (i.e.
	    distutils.sysconfig.customize_compiler) run on it. So instead of going
	    the OO route, I have this. Note, it's kindof like a wierd functional
	    subclassing going on."""

	    # tell the compiler it can processes .cu
	    self.src_extensions.append('.cu')

	    # save references to the default compiler_so and _comple methods
	    default_compiler_so = self.compiler_so
	    super = self._compile

	    # now redefine the _compile method. This gets executed for each
	    # object but distutils doesn't have the ability to change compilers
	    # based on source extension: we add it.
	    def _compile(obj, src, ext, cc_args, extra_postargs, pp_opts):
	        if os.path.splitext(src)[1] == '.cu':
	            # use the cuda for .cu files
	            self.set_executable('compiler_so', CUDA['nvcc'])
	            # use only a subset of the extra_postargs, which are 1-1 translated
	            # from the extra_compile_args in the Extension class
	            postargs = extra_postargs['nvcc']
	        else:
	            postargs = extra_postargs['gcc']

	        super(obj, src, ext, cc_args, postargs, pp_opts)
	        # reset the default compiler_so, which we might have changed for cuda
	        self.compiler_so = default_compiler_so

	    # inject our redefined _compile method into the class
	    self._compile = _compile

	# run the customize_compiler
	class custom_build_ext(build_ext):
	    def build_extensions(self):
	        customize_compiler_for_nvcc(self.compiler)
	        build_ext.build_extensions(self)

	CUDA = locate_cuda()

	return CUDA, custom_build_ext