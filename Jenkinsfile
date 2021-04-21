#!/usr/bin/env groovy

def RPMFetchSource() {
    dir ('source') {
	checkout([
	    $class: 'GitSCM',
	    branches: [
		[ name: '*/master' ]
	    ],
	    extensions: [
		[
		    $class: 'CloneOption',
		    timeout: 60
                ],[
                    $class: 'SubmoduleOption',
                    timeout: 60
		]
	    ],
	    userRemoteConfigs: [
		[ url: 'git://git.kraxel.org/mirror/edk2.git' ]
	    ]])
    }
}

def RPMBuildSource() {
    sh '''
	# cleanup
	rm -rf rpms

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

        # edk2 build uses WORKSPACE too ...
        WS="$WORKSPACE"
        unset WORKSPACE

	# install deps
	/usr/local/bin/configure-mirror
	cp firmware.repo /etc/yum.repos.d
	dnf builddep -y *.spec

        # build source package
        rpmbuild                                     \
            --define "_specdir ${WS}"                \
            --define "_sourcedir ${WS}"              \
            --define "_rpmdir ${WS}/rpms"            \
            --define "_srcrpmdir ${WS}/rpms/src"     \
            --define "_builddir ${WS}/rpms/build"    \
            --define "_buildrootdir ${WS}/rpms/root" \
            -bs *.spec

        # drop spec file changes
        git reset --hard
	'''
//    archiveArtifacts 'rpms/src/*.src.rpm'
//    stash name: 'srpm', includes: 'rpms/src/*.src.rpm'
}

def RPMBuildBinary(arch) {
//    unstash 'srpm'
    sh '''
        # edk2 build uses WORKSPACE too ...
        WS="$WORKSPACE"
        unset WORKSPACE

        # build binary package
        rpmbuild                                     \
            --define "_specdir ${WS}"                \
            --define "_sourcedir ${WS}"              \
            --define "_rpmdir ${WS}/rpms"            \
            --define "_srcrpmdir ${WS}/rpms/src"     \
            --define "_builddir ${WS}/rpms/build"    \
            --define "_buildrootdir ${WS}/rpms/root" \
            --rebuild rpms/src/*.src.rpm
	'''
    archiveArtifacts "rpms/$arch/*,rpms/noarch/*"
}

pipeline {
    agent {
        docker {
            image 'registry.gitlab.com/kraxel/rpm-package-builder:fedora'
            args '-u root'
        }
    }

    options {
	buildDiscarder(logRotator(numToKeepStr: '5'))
	disableConcurrentBuilds()
    }

    triggers {
	pollSCM('H H(0-3) * * *')
    }

    stages {

	stage ('git+srpm') {
	    steps {
		RPMFetchSource();
		RPMBuildSource()
	    }
	}

	stage ("rpms") {
	    steps {
		RPMBuildBinary('x86_64')
	    }
	}
    }

//    post {
//	failure {
//	    emailext([
//		to: 'builds@kraxel.org,lersek@redhat.com',
//		subject: "${JOB_NAME} - build #${BUILD_NUMBER} - FAILED!",
//		body: "${BUILD_URL}\n",
//		attachLog: true,
//	    ])
//	}
//	always {
//	    mail to: 'builds@kraxel.org',
//		subject: "Status of pipeline: ${currentBuild.fullDisplayName}",
//		body: "${env.BUILD_URL} has result ${currentBuild.result}"
//	}
//    }
}
