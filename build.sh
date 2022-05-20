#!/bin/sh
WS="/root/edk2/"
TAG="edk2-stable202102"
BUILD_NUMBER="1"

fetch_source() {
    mkdir -p "source"
    if [ "`ls -A ./source`" = "" ]; then
        git clone -b ${TAG} https://github.com/tianocore/edk2.git --recurse-submodules ./source
            if (( $? != 0 )); then
            echo "fetch edk2 source code failed"
            exit 1
        fi
    fi
}

rpm_build_source() {
    rm -rf ./rpms

    # figure version
    ghash="g$(cd source; git show --format='format:%h' | head -1)"
    gcnt="$(git show --format='format:%ai' | head -1 | sed -e 's/ .*//' -e 's/-//g')"
    version="0"

    # fresh snapshot tarball
    rm -f *.tar.gz
    tarball="edk2-${ghash}.tar.gz"
    (cd source; git archive --format=tar --prefix="${tarball%.tar.gz}/" HEAD) \
            > "${tarball%.gz}"
    (cd source/CryptoPkg/Library/OpensslLib/openssl; git archive --format=tar \
        --prefix="${tarball%.tar.gz}/CryptoPkg/Library/OpensslLib/openssl/" \
            HEAD) > "openssl.tar"
    (cd source/ArmPkg/Library/ArmSoftFloatLib/berkeley-softfloat-3; git archive --format=tar \
        --prefix="${tarball%.tar.gz}/ArmPkg/Library/ArmSoftFloatLib/berkeley-softfloat-3/" \
            HEAD) > "softfloat.tar"
    tar --concatenate --file "${tarball%.gz}" "openssl.tar"
    tar --concatenate --file "${tarball%.gz}" "softfloat.tar"
    rm "openssl.tar"
    gzip "${tarball%.gz}"
    # generate spec file from template
    sed -e "s/\\(Version:[ \\t]\\+\\)\\(.*\\)/\\1${version}/" \
        -e "s/\\(Release:[ \\t]\\+\\)\\(.*\\)/\\1${gcnt}.${BUILD_NUMBER}.${ghash}/" \
        -e "s/\\(Source0:[ \\t]\\+\\)\\(.*\\)/\\1${tarball}/" \
        -e "s/\\(%setup\\)\\(.*\\)/\\1 -q -n ${tarball%.tar.gz}/" \
        < edk2.git.spec.template > edk2.git.spec
    diff -u edk2.git.spec.template edk2.git.spec || true

    # build source package
    rpmbuild                                     \
        --define "_specdir ${WS}"                \
        --define "_sourcedir ${WS}"              \
        --define "_rpmdir ${WS}/rpms"            \
        --define "_srcrpmdir ${WS}/rpms/src"     \
        --define "_builddir ${WS}/rpms/build"    \
        --define "_buildrootdir ${WS}/rpms/root" \
        -bs *.spec
}

rpm_build_binary() {
    # build binary package
    rpmbuild                                     \
        --define "_specdir ${WS}"                \
        --define "_sourcedir ${WS}"              \
        --define "_rpmdir ${WS}/rpms"            \
        --define "_srcrpmdir ${WS}/rpms/src"     \
        --define "_builddir ${WS}/rpms/build"    \
        --define "_buildrootdir ${WS}/rpms/root" \
        --rebuild rpms/src/*.src.rpm
}

fetch_source
rpm_build_source
rpm_build_binary
