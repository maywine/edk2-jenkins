#!/bin/sh
if test "$1" = ""; then
	echo "usage: $0 <version>"
	exit 1
fi
wget "https://openssl.org/source/openssl-${1}.tar.gz"
