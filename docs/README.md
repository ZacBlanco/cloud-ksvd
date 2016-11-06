## Code Documentation

The python implementation of Cloud K-SVD can be found under `../cloud_ksvd`.

You'll need to install sphinx and the sphinx RTD theme

    pip3 install sphinx sphinx_rtd_theme

You can generate and build the documentation for all of the code with the following commands

    cd ./docs
    make clean
    sphinx-apidoc -e -f -o ./source/autodoc/cloud_ksvd ../cloud_ksvd/
    make html

#### One liner

Assumes you're already in the `docs/` directory

    make clean; sphinx-apidoc -e -f -o ./source/autodoc/cloud_ksvd ../cloud_ksvd/; make html 


## Viewing Documentation

After running the commands above, you can 