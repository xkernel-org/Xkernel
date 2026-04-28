pushd kfuncs && make -j CC="${CC:-gcc}" && popd
pushd consistency && make -j CC="${CC:-gcc}" && popd