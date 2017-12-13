import os
from numpy.distutils.misc_util import Configuration

def configuration(parent_package='', top_path=None):
    config = Configuration('sklgpu', parent_package, top_path)

    config.add_subpackage('tree')
    config.add_subpackage('ensemble')

    return config

if __name__ == '__main__':
    from distutils.core import setup
    setup(**configuration(top_path='').todict())