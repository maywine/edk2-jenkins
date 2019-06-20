%global debug_package %{nil}

Name:		edk2.git
Version:	0
Release:	20130809.b0.g9b141c5%{?dist}
Summary:	EFI Development Kit II

Group:		Applications/Emulators
License:	BSD and OpenSSL
URL:		http://sourceforge.net/apps/mediawiki/tianocore/index.php?title=EDK2
Source0:	edk2.git-g9b141c5.tar.xz
Source1:	qemu-boot-kernel
Source9:	descriptor-edk2.pl

Patch3:         0001-OvmfPkg-don-t-lock-lock-umb-when-running-csm.patch
Patch4:		0001-MdeModulePkg-TerminalDxe-add-other-text-resolutions.patch
Patch5:		0001-EXCLUDE_SHELL_FROM_FD.patch

Patch10:	0001-OvmfPkg-SmbiosPlatformDxe-install-legacy-QEMU-tables.patch
Patch11:	0002-OvmfPkg-SmbiosPlatformDxe-install-patch-default-lega.patch
Patch12:	0003-OvmfPkg-SmbiosPlatformDxe-install-patch-default-lega.patch

Patch30:	0001-tools_def.template-take-GCC4-_-IA32-X64-prefixes-fro.patch

BuildRequires:	iasl
BuildRequires:	nasm
BuildRequires:	python
BuildRequires:	libuuid-devel
BuildRequires:	seabios.git-csm
BuildRequires:	gcc-arm-linux-gnu binutils-arm-linux-gnu
BuildRequires:	gcc-aarch64-linux-gnu binutils-aarch64-linux-gnu
BuildRequires:	dosfstools
BuildRequires:	mtools
BuildRequires:	genisoimage

# for check
BuildRequires:	qemu-kvm

%description
EFI Development Kit II

%package tools
Summary:	EFI Development Kit II Tools
%description tools
EFI Development Kit II Tools

%package ovmf-ia32
Summary:	Open Virtual Machine Firmware
License:	BSD License (no advertising) with restrictions on use and redistribution
BuildArch:      noarch
%description ovmf-ia32
EFI Development Kit II
Open Virtual Machine Firmware
32bit version

%package ovmf-x64
Summary:	Open Virtual Machine Firmware
License:	BSD License (no advertising) with restrictions on use and redistribution
BuildArch:      noarch
%description ovmf-x64
EFI Development Kit II
Open Virtual Machine Firmware
64bit version

%package arm
Summary:	Open Virtual Machine Firmware
License:	BSD License (no advertising) with restrictions on use and redistribution
BuildArch:      noarch
%description arm
EFI Development Kit II
ARM UEFI Firmware

%package aarch64
Summary:	Open Virtual Machine Firmware
License:	BSD License (no advertising) with restrictions on use and redistribution
BuildArch:      noarch
%description aarch64
EFI Development Kit II
AARCH64 UEFI Firmware

%prep
%setup -q -n %{name}
%patch3 -p1
%patch4 -p1
%patch5 -p1
%patch10 -p1
%patch11 -p1
%patch12 -p1
%patch30 -p1

%build
source ./edksetup.sh

# figure tools switch
GCCVER=$(gcc --version | awk '{ print $3; exit}')
case "$GCCVER" in
4.4*)	CC_FLAGS="-t GCC44";;
4.5*)	CC_FLAGS="-t GCC45";;
4.6*)	CC_FLAGS="-t GCC46";;
4.7*)	CC_FLAGS="-t GCC47";;
4.8*)	CC_FLAGS="-t GCC48";;
4.9*)	CC_FLAGS="-t GCC49";;
5.*)	CC_FLAGS="-t GCC5";;
6.*)	CC_FLAGS="-t GCC5";;
7.*)	CC_FLAGS="-t GCC5";;
8.*)	CC_FLAGS="-t GCC5";;
9.*)	CC_FLAGS="-t GCC5";;
esac

CROSSGCCVER=$(arm-linux-gnu-gcc --version | awk '{ print $3; exit}')
case "$CROSSGCCVER" in
4.8*)	CROSS_CC_FLAGS="-t GCC48"
        export GCC48_ARM_PREFIX="arm-linux-gnu-"
        export GCC48_AARCH64_PREFIX="aarch64-linux-gnu-"
        ;;
4.9*)
	CROSS_CC_FLAGS="-t GCC49"
        export GCC49_ARM_PREFIX="arm-linux-gnu-"
        export GCC49_AARCH64_PREFIX="aarch64-linux-gnu-"
        ;;
5.* | 6.* | 7.* | 8.*)
	CROSS_CC_FLAGS="-t GCC5"
        export GCC5_ARM_PREFIX="arm-linux-gnu-"
        export GCC5_AARCH64_PREFIX="aarch64-linux-gnu-"
        ;;
esac

# parallel builds
SMP_MFLAGS="%{?_smp_mflags}"
if [[ x"$SMP_MFLAGS" = x-j* ]]; then
	CC_FLAGS="$CC_FLAGS -n ${SMP_MFLAGS#-j}"
	CROSS_CC_FLAGS="$CROSS_CC_FLAGS -n ${SMP_MFLAGS#-j}"
elif [ -n "%{?jobs}" ]; then
	CC_FLAGS="$CC_FLAGS -n %{?jobs}"
	CROSS_CC_FLAGS="$CROSS_CC_FLAGS -n %{?jobs}"
fi

# prepare
cp /usr/share/seabios.git-csm/bios-csm.bin OvmfPkg/Csm/Csm16/Csm16.bin
make -C BaseTools

# build key encollment boot iso
build_iso()
{
	local ARCH="$1"
	local UEFI_BINDIR=$(
		echo -n Build/Ovmf${ARCH}/DEBUG_*/
		echo $ARCH | tr '[:lower:'] '[:upper:]'
	)
	local UEFI_SHELL_BINARY=$UEFI_BINDIR/Shell.efi
	local ENROLLER_BINARY=$UEFI_BINDIR/EnrollDefaultKeys.efi
	local UEFI_SHELL_IMAGE=uefi_shell_${ARCH}.img
	local ISO_IMAGE=ovmf-$(
		echo $ARCH | tr '[:upper:]' '[:lower:']
	)/UefiShell.iso

	local UEFI_SHELL_BINARY_BNAME=$(basename -- "$UEFI_SHELL_BINARY")
	local UEFI_SHELL_SIZE=$(stat --format=%s -- "$UEFI_SHELL_BINARY")
	local ENROLLER_SIZE=$(stat --format=%s -- "$ENROLLER_BINARY")

	# add 1MB then 10% for metadata
	local UEFI_SHELL_IMAGE_KB=$((
		(UEFI_SHELL_SIZE + ENROLLER_SIZE +
		 1 * 1024 * 1024) * 11 / 10 / 1024
	))

	# create non-partitioned FAT image
	rm -f -- "$UEFI_SHELL_IMAGE"
	/usr/sbin/mkdosfs -C "$UEFI_SHELL_IMAGE" -n UEFI_SHELL -- "$UEFI_SHELL_IMAGE_KB"

	export MTOOLS_SKIP_CHECK=1
	mmd	-i "$UEFI_SHELL_IMAGE"				::efi
	mmd	-i "$UEFI_SHELL_IMAGE"				::efi/boot
	mcopy	-i "$UEFI_SHELL_IMAGE"	"$UEFI_SHELL_BINARY"	::efi/boot/bootx64.efi
	mcopy	-i "$UEFI_SHELL_IMAGE"	"$ENROLLER_BINARY"	::
	mdir	-i "$UEFI_SHELL_IMAGE"	-/			::

	# build ISO with FAT image file as El Torito EFI boot image
	genisoimage -input-charset ASCII -J -rational-rock \
		-efi-boot "$UEFI_SHELL_IMAGE" -no-emul-boot \
		-o "$ISO_IMAGE" -- "$UEFI_SHELL_IMAGE"
}

# build ovmf
for cfg in pure-efi with-csm need-smm; do
	OVMF_FLAGS="$CC_FLAGS -D HTTP_BOOT_ENABLE -D FD_SIZE_2MB"

	case "$cfg" in
	with-csm)
		OVMF_FLAGS="$OVMF_FLAGS -D CSM_ENABLE"
		;;
	pure-efi)
		# nothing
		;;
	need-smm)
		OVMF_FLAGS="$OVMF_FLAGS -D SECURE_BOOT_ENABLE"
		OVMF_FLAGS="$OVMF_FLAGS -D SMM_REQUIRE"
		OVMF_FLAGS="$OVMF_FLAGS -D EXCLUDE_SHELL_FROM_FD"
		;;
	esac

	build $OVMF_FLAGS -a IA32 -p OvmfPkg/OvmfPkgIa32.dsc
	mkdir -p "ovmf-ia32"
	cp Build/OvmfIa32/DEBUG_*/FV/OVMF.fd ovmf-ia32/OVMF-${cfg}.fd
	cp Build/OvmfIa32/DEBUG_*/FV/OVMF_CODE.fd ovmf-ia32/OVMF_CODE-${cfg}.fd
	cp Build/OvmfIa32/DEBUG_*/FV/OVMF_VARS.fd ovmf-ia32/OVMF_VARS-${cfg}.fd
	if [ "$cfg" = need-smm ]; then
		build_iso Ia32
	fi
	rm -rf Build/OvmfIa32

	build $OVMF_FLAGS -a X64 -p OvmfPkg/OvmfPkgX64.dsc
	mkdir -p "ovmf-x64"
	cp Build/OvmfX64/DEBUG_*/FV/OVMF.fd ovmf-x64/OVMF-${cfg}.fd
	cp Build/OvmfX64/DEBUG_*/FV/OVMF_CODE.fd ovmf-x64/OVMF_CODE-${cfg}.fd
	cp Build/OvmfX64/DEBUG_*/FV/OVMF_VARS.fd ovmf-x64/OVMF_VARS-${cfg}.fd
	if [ "$cfg" = need-smm ]; then
		build_iso X64
	fi
	rm -rf Build/OvmfX64
done

# build arm/aarch64 firmware
ARM_FLAGS="$CROSS_CC_FLAGS"
build $ARM_FLAGS -a ARM \
    -D DEBUG_PRINT_ERROR_LEVEL=0x8040004F \
    -D HTTP_BOOT_ENABLE \
    -p ArmVirtPkg/ArmVirtQemu.dsc
build $ARM_FLAGS -a AARCH64 \
    -D DEBUG_PRINT_ERROR_LEVEL=0x8040004F \
    -D HTTP_BOOT_ENABLE \
    -p ArmVirtPkg/ArmVirtQemu.dsc
mkdir -p "arm" "aarch64"
cp Build/ArmVirtQemu-ARM/DEBUG_*/FV/*.fd arm
cp Build/ArmVirtQemu-AARCH64/DEBUG_*/FV/*.fd aarch64
for fd in {arm,aarch64}/QEMU_EFI.fd; do
	code="${fd%.fd}-pflash.raw"
	vars="${fd%%/*}/vars-template-pflash.raw"
	dd of="$code" if="/dev/zero" bs=1M count=64
	dd of="$code" if="$fd" conv=notrunc
	dd of="$vars" if="/dev/zero" bs=1M count=64
	dd of="$vars" if="${fd//QEMU_EFI/QEMU_VARS}" conv=notrunc
done

%check

# x86 pc
for cfg in pure-efi with-csm; do
	for cpus in 1 4; do
		%{SOURCE1} -M pc -smp $cpus \
			-bios ovmf-x64/OVMF-${cfg}.fd
	done
done

# x86 q35
for cfg in pure-efi with-csm need-smm; do
	for cpus in 1 4; do
		cp ovmf-x64/OVMF_CODE-${cfg}.fd boot-test-code-${cfg}.raw
		cp ovmf-x64/OVMF_VARS-${cfg}.fd boot-test-vars-${cfg}.raw
		%{SOURCE1} -M q35,smm=on -smp $cpus \
		  -global ICH9-LPC.disable_s3=1 \
		  -drive file=boot-test-code-${cfg}.raw,if=pflash,format=raw,unit=0,readonly=on \
		  -drive file=boot-test-vars-${cfg}.raw,if=pflash,format=raw,unit=1
	done
done


%install
mkdir -p %{buildroot}%{_bindir}
install	--strip \
	BaseTools/Source/C/bin/EfiRom \
	BaseTools/Source/C/bin/VolInfo \
	%{buildroot}%{_bindir}

mkdir -p %{buildroot}/usr/share/%{name}
#cp -a ovmf-* arm aarch64 coreboot-* %{buildroot}/usr/share/%{name}
cp -a ovmf-* arm aarch64 %{buildroot}/usr/share/%{name}

mkdir -p %{buildroot}/usr/share/qemu/firmware
%{SOURCE9} %{buildroot}/usr/share/qemu/firmware

%files
%dir /usr/share/%{name}

%files tools
%doc BaseTools/UserManuals/EfiRom_Utility_Man_Page.rtf
%doc BaseTools/UserManuals/VolInfo_Utility_Man_Page.rtf
%{_bindir}/*

%files ovmf-ia32
%doc OvmfPkg/README
%dir /usr/share/%{name}
/usr/share/%{name}/ovmf-ia32
/usr/share/qemu/firmware/90-ovmf-ia32-git-*.json

%files ovmf-x64
%doc OvmfPkg/README
%dir /usr/share/%{name}
/usr/share/%{name}/ovmf-x64
/usr/share/qemu/firmware/90-ovmf-x64-git-*.json

%files arm
%dir /usr/share/%{name}
/usr/share/%{name}/arm
/usr/share/qemu/firmware/90-uefi-arm-git.json

%files aarch64
%dir /usr/share/%{name}
/usr/share/%{name}/aarch64
/usr/share/qemu/firmware/90-uefi-a64-git.json

%changelog
