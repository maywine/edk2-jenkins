#!/usr/bin/env groovy

def RPMSource() {
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
		]
	    ],
	    userRemoteConfigs: [
		[ url: 'git://github.com/tianocore/edk2.git' ]
	    ]])
    }
}

def RPMBuild() {
    sh '''
        # figure version
        ghash="g$(cd source; git show --format="format:%h" | head -1)"
        gcnt="0"
        version="0"

        # fresh snapshot tarball
        rm -f *.tar.gz
        tarball="edk2-${ghash}.tar.gz"
        (cd source; git archive --format=tar --prefix="${tarball%.tar.gz}/" HEAD) \
                | gzip > "${tarball}"

        # tweak spec file
        sed -i.orig \
            -e "s/\\(Version:[ \\t]\\+\\)\\(.*\\)/\\1${version}/" \
            -e "s/\\(Release:[ \\t]\\+\\)\\(.*\\)/\\1${gcnt}.${BUILD_NUMBER}.${ghash}/" \
            -e "s/\\(Source0:[ \\t]\\+\\)\\(.*\\)/\\1${tarball}/" \
            -e "s/\\(%setup\\)\\(.*\\)/\\1 -n ${tarball%.tar.gz}/" \
            *.spec
        diff -u *.spec.orig *.spec || true

        # build package
        rpmbuild                                            \
            --define "_specdir ${WORKSPACE}"                \
            --define "_sourcedir ${WORKSPACE}"              \
            --define "_rpmdir ${WORKSPACE}/rpms"            \
            --define "_srcrpmdir ${WORKSPACE}/rpms/src"     \
            --define "_builddir ${WORKSPACE}/build"         \
            --define "_buildrootdir ${WORKSPACE}/buildroot" \
            -ba *.spec

        # revert spec file tweaks
        git reset --hard

        # create rpm package repo
	createrepo rpms
	'''
    archiveArtifacts 'rpms/*/*'
}

def RPMCleanup() {
    dir ("build") {
	deleteDir()
    }
    dir ("buildroot") {
	deleteDir()
    }
    dir ("rpms") {
	deleteDir()
    }
}

pipeline {
    agent {
	node 'sys-fedora-x64'
    }

    options {
	buildDiscarder(logRotator(numToKeepStr: '3'))
	disableConcurrentBuilds()
    }

    triggers {
	pollSCM('H * * * *')
    }

    stages {

	stage ('Prepare') {
	    steps {
		RPMSource();
	    }
	}

	stage ("RPM Build") {
	    steps {
		RPMBuild()
	    }
	}

	stage ("Cleanup") {
	    steps {
		RPMCleanup()
	    }
	}
    }

    post {
	failure {
	    emailext([
		to: 'kraxel@gmail.com',
		subject: "${JOB_NAME} - build #${BUILD_NUMBER} - FAILED!",
		body: "${BUILD_URL}\n",
		attachLog: true,
	    ])
	}
    }
}
