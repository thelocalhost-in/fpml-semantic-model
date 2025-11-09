from setuptools import setup, find_packages
import os

# Utility function to read the README file and update.
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name='fpml-semantic-model',
    version='v0.2.2',
    author='thelocalhost-in',
    author_email='thelocalhost.in@gmail.com',
    description='A semantic search and structural analysis model for FpML XSD schemas.',
    long_description=read('README.md'), 
    long_description_content_type='text/markdown',
    url='https://github.com/thelocalhost-in/fpml-semantic-model', # Replace with your GitHub repository URL
    packages=find_packages(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Financial and Insurance Industry',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Topic :: Text Processing',
        'Topic :: Scientific/Engineering :: Information Analysis',
    ],
    keywords='fpml xsd xml finance machine-learning semantic-search',
    install_requires=[
        # Core ML dependencies for the SemanticSearchModel
    ],
    # Include non-code files (like your all_xsd_data.json)
    package_data={
        'fpml_semantic_model': ['all_xsd_data.json'],
    },
    include_package_data=True,
    python_requires='>=3.8',
)