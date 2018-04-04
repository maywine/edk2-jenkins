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
		sh 'echo foobar'
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
