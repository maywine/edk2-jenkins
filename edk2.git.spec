%global debug_package %{nil}

Name:		edk2.git
Version:	0
Release:	20130809.b0.g9b141c5%{?dist}
Summary:	EFI Development Kit II

Group:		Applications/Emulators
License:	BSD License (two clause)
URL:		http://sourceforge.net/apps/mediawiki/tianocore/index.php?title=EDK2
Source0:	edk2.git-g9b141c5.tar.xz
Source1:	openssl-0.9.8zb.tar.gz
Patch1:         0001-OvmfPkg-Don-t-build-in-QemuVideoDxe-when-we-have-CSM.patch
Patch2:         0001-pick-up-any-display-device-not-only-vga.patch
Patch3:         edk2-no-lock-umb.patch
Patch4:		0001-MdeModulePkg-TerminalDxe-add-other-text-resolutions.patch

Patch10:	0001-OvmfPkg-SmbiosPlatformDxe-install-legacy-QEMU-tables.patch
Patch11:	0002-OvmfPkg-SmbiosPlatformDxe-install-patch-default-lega.patch
Patch12:	0003-OvmfPkg-SmbiosPlatformDxe-install-patch-default-lega.patch

Patch90:        coreboot-pkg.patch

BuildRequires:	iasl
BuildRequires:	python
BuildRequires:	libuuid-devel
BuildRequires:	seabios.git-csm

%description
EFI Development Kit II

%package tools
Summary:	EFI Development Kit II Tools
%description tools
EFI Development Kit II Tools

%package ovmf-ia32
Summary:	Open Virtual Machine Firmware
Requires:       %{name}
Requires:       ipxe.git-combined
Requires:       seavgabios.git
License:	BSD License (no advertising) with restrictions on use and redistribution
%description ovmf-ia32
EFI Development Kit II
Open Virtual Machine Firmware
32bit version

%ifarch x86_64
%package ovmf-x64
Summary:	Open Virtual Machine Firmware
Requires:       %{name}
Requires:       ipxe.git-combined
Requires:       seavgabios.git
License:	BSD License (no advertising) with restrictions on use and redistribution
%description ovmf-x64
EFI Development Kit II
Open Virtual Machine Firmware
64bit version
%endif

#%package coreboot
#Summary:	coreboot payloads
#Requires:       %{name}
#License:	BSD License (no advertising) with restrictions on use and redistribution
#%description coreboot
#EFI Development Kit II
#coreboot payloads

%prep
%setup -q -n %{name}
%patch1 -p1
%patch2 -p1
%patch3 -p1
%patch4 -p1
%patch10 -p1
%patch11 -p1
%patch12 -p1
#%patch90 -p1

# add openssl
tar -C CryptoPkg/Library/OpensslLib -xf %{SOURCE1}
(cd CryptoPkg/Library/OpensslLib/openssl-0.9.8zb;
 patch -p0 < ../EDKII_openssl-0.9.8zb.patch)
(cd CryptoPkg/Library/OpensslLib; ./Install.sh)

%build
source ./edksetup.sh

if test -f /opt/rh/devtoolset-2/enable; then
        source /opt/rh/devtoolset-2/enable
	prefix=$(dirname $(which gcc))/
else
	prefix=/usr/bin/
fi

# figure tools switch
GCCVER=$(gcc --version | awk '{ print $3; exit}')
case "$GCCVER" in
4.4*)	CC_FLAGS="-t GCC44";;
4.5*)	CC_FLAGS="-t GCC45";;
4.6*)	CC_FLAGS="-t GCC46";;
4.7*)	CC_FLAGS="-t GCC47";;
4.8*)	CC_FLAGS="-t GCC48";;
esac
sed -i.bak -e "s|\(^DEFINE GCC48_.*_PREFIX.*=\).*|\1 $prefix|" Conf/tools_def.txt

# parallel builds
SMP_MFLAGS="%{?_smp_mflags}"
if [[ x"$SMP_MFLAGS" = x-j* ]]; then
	CC_FLAGS="$CC_FLAGS -n ${SMP_MFLAGS#-j}"
elif [ -n "%{?jobs}" ]; then
	CC_FLAGS="$CC_FLAGS -n %{?jobs}"
fi

# prepare
cp /usr/share/seabios.git-csm/bios-csm.bin OvmfPkg/Csm/Csm16/Csm16.bin
#cp /usr/share/seabios.git-csm/bios-csm.bin corebootPkg/Csm/Csm16/Csm16.bin
make -C BaseTools

# go build
for cfg in pure-efi with-csm; do
	OVMF_FLAGS="$CC_FLAGS -D BUILD_NEW_SHELL -D SECURE_BOOT_ENABLE -D FD_SIZE_2MB"
	CORE_FLAGS="$CC_FLAGS -D BUILD_NEW_SHELL -D NETWORK_ENABLE=TRUE"

	case "$cfg" in
	with-csm)
		OVMF_FLAGS="$OVMF_FLAGS -D CSM_ENABLE"
		CORE_FLAGS="$CORE_FLAGS -D CSM_ENABLE=TRUE"
		;;
	pure-efi)
		# nothing
		;;
	esac

	build $OVMF_FLAGS -a IA32 -p OvmfPkg/OvmfPkgIa32.dsc
	mkdir -p "ovmf-ia32"
	cp Build/OvmfIa32/DEBUG_*/FV/OVMF.fd ovmf-ia32/OVMF-${cfg}.fd
	cp Build/OvmfIa32/DEBUG_*/FV/OVMF_CODE.fd ovmf-ia32/OVMF_CODE-${cfg}.fd
	cp Build/OvmfIa32/DEBUG_*/FV/OVMF_VARS.fd ovmf-ia32/OVMF_VARS-${cfg}.fd
	rm -rf Build/OvmfIa32

#	build $CORE_FLAGS -a IA32 -p corebootPkg/corebootPkg.dsc
#	mkdir -p "coreboot-ia32"
#	cp Build/corebootIA32/DEBUG_*/FV/COREBOOT.fd coreboot-ia32/COREBOOT-${cfg}.fd
#	rm -rf Build/corebootIa32

%ifarch x86_64
	build $OVMF_FLAGS -a X64 -p OvmfPkg/OvmfPkgX64.dsc
	mkdir -p "ovmf-x64"
	cp Build/OvmfX64/DEBUG_*/FV/OVMF.fd ovmf-x64/OVMF-${cfg}.fd
	cp Build/OvmfX64/DEBUG_*/FV/OVMF_CODE.fd ovmf-x64/OVMF_CODE-${cfg}.fd
	cp Build/OvmfX64/DEBUG_*/FV/OVMF_VARS.fd ovmf-x64/OVMF_VARS-${cfg}.fd
	rm -rf Build/OvmfX64

#	build $CORE_FLAGS -a X64 -p corebootPkg/corebootPkg.dsc
#	mkdir -p "coreboot-x64"
#	cp Build/corebootX64/DEBUG_*/FV/COREBOOT.fd coreboot-x64/COREBOOT-${cfg}.fd
#	rm -rf Build/corebootX64
%endif
done

%install
mkdir -p %{buildroot}%{_bindir}
install	--strip \
	BaseTools/Source/C/bin/EfiRom \
	BaseTools/Source/C/bin/VolInfo \
	%{buildroot}%{_bindir}

mkdir -p %{buildroot}/usr/share/%{name}/ovmf-ia32
cp	ovmf-ia32/* \
	%{buildroot}/usr/share/%{name}/ovmf-ia32
ln -s	OVMF-with-csm.fd \
	%{buildroot}/usr/share/%{name}/ovmf-ia32/bios.bin
ln -s	OVMF-with-csm.fd \
	%{buildroot}/usr/share/%{name}/ovmf-ia32/bios-256k.bin

for ext in rom bin; do
  ln -s	../../ipxe.git/combined/8086100e.rom \
	%{buildroot}/usr/share/%{name}/ovmf-ia32/pxe-e1000.$ext
  ln -s	../../ipxe.git/combined/10ec8029.rom \
	%{buildroot}/usr/share/%{name}/ovmf-ia32/pxe-ne2k_pci.$ext
  ln -s	../../ipxe.git/combined/10222000.rom \
	%{buildroot}/usr/share/%{name}/ovmf-ia32/pxe-pcnet.$ext
  ln -s	../../ipxe.git/combined/10ec8139.rom \
	%{buildroot}/usr/share/%{name}/ovmf-ia32/pxe-rtl8139.$ext
  ln -s	../../ipxe.git/combined/1af41000.rom \
	%{buildroot}/usr/share/%{name}/ovmf-ia32/pxe-virtio.$ext
done
for ext in rom; do
  ln -s	../../ipxe.git/combined/8086100e.rom \
	%{buildroot}/usr/share/%{name}/ovmf-ia32/efi-e1000.$ext
  ln -s	../../ipxe.git/combined/10ec8029.rom \
	%{buildroot}/usr/share/%{name}/ovmf-ia32/efi-ne2k_pci.$ext
  ln -s	../../ipxe.git/combined/10222000.rom \
	%{buildroot}/usr/share/%{name}/ovmf-ia32/efi-pcnet.$ext
  ln -s	../../ipxe.git/combined/10ec8139.rom \
	%{buildroot}/usr/share/%{name}/ovmf-ia32/efi-rtl8139.$ext
  ln -s	../../ipxe.git/combined/1af41000.rom \
	%{buildroot}/usr/share/%{name}/ovmf-ia32/efi-virtio.$ext
done

for vga in stdvga cirrus vmware qxl virtio; do
	ln -s	../../seavgabios.git/vgabios-$vga.bin \
		%{buildroot}/usr/share/%{name}/ovmf-ia32/vgabios-$vga.bin
done

%ifarch x86_64
mkdir -p %{buildroot}/usr/share/%{name}/ovmf-x64
cp	ovmf-x64/* \
	%{buildroot}/usr/share/%{name}/ovmf-x64
ln -s	OVMF-with-csm.fd \
	%{buildroot}/usr/share/%{name}/ovmf-x64/bios.bin

for ext in rom bin; do
  ln -s	../../ipxe.git/combined/8086100e.rom \
	%{buildroot}/usr/share/%{name}/ovmf-x64/pxe-e1000.$ext
  ln -s	../../ipxe.git/combined/10ec8029.rom \
	%{buildroot}/usr/share/%{name}/ovmf-x64/pxe-ne2k_pci.$ext
  ln -s	../../ipxe.git/combined/10222000.rom \
	%{buildroot}/usr/share/%{name}/ovmf-x64/pxe-pcnet.$ext
  ln -s	../../ipxe.git/combined/10ec8139.rom \
	%{buildroot}/usr/share/%{name}/ovmf-x64/pxe-rtl8139.$ext
  ln -s	../../ipxe.git/combined/1af41000.rom \
	%{buildroot}/usr/share/%{name}/ovmf-x64/pxe-virtio.$ext
done
for ext in rom; do
  ln -s	../../ipxe.git/combined/8086100e.rom \
	%{buildroot}/usr/share/%{name}/ovmf-x64/efi-e1000.$ext
  ln -s	../../ipxe.git/combined/10ec8029.rom \
	%{buildroot}/usr/share/%{name}/ovmf-x64/efi-ne2k_pci.$ext
  ln -s	../../ipxe.git/combined/10222000.rom \
	%{buildroot}/usr/share/%{name}/ovmf-x64/efi-pcnet.$ext
  ln -s	../../ipxe.git/combined/10ec8139.rom \
	%{buildroot}/usr/share/%{name}/ovmf-x64/efi-rtl8139.$ext
  ln -s	../../ipxe.git/combined/1af41000.rom \
	%{buildroot}/usr/share/%{name}/ovmf-x64/efi-virtio.$ext
done

for vga in stdvga cirrus vmware qxl virtio; do
	ln -s	../../seavgabios.git/vgabios-$vga.bin \
		%{buildroot}/usr/share/%{name}/ovmf-x64/vgabios-$vga.bin
done
%endif

#cp -a	coreboot-* \
#	%{buildroot}/usr/share/%{name}

%files
%doc OvmfPkg/README
%dir /usr/share/%{name}

%files tools
%doc OvmfPkg/License.txt
%doc BaseTools/UserManuals/EfiRom_Utility_Man_Page.rtf
%doc BaseTools/UserManuals/VolInfo_Utility_Man_Page.rtf
%{_bindir}/*

%files ovmf-ia32
%doc FatBinPkg/License.txt
/usr/share/%{name}/ovmf-ia32

%ifarch x86_64
%files ovmf-x64
%doc FatBinPkg/License.txt
/usr/share/%{name}/ovmf-x64
%endif

#%files coreboot
#/usr/share/%{name}/coreboot-*

%changelog
