#!/usr/bin/perl
use strict;
use warnings;
use JSON;

my $dest = shift;
$dest = "/usr/share/qemu/firmware/" unless defined($dest);

my $base = "/usr/share/edk2.git/";
my $json = JSON->new->allow_nonref;

sub write_file {
	my $file = shift;
	my $desc = shift;
	my $target = shift;
	my $code = shift;
	my $vars = shift;
	my $features = shift;
	my $interfaces = shift;
	my $info;

	$features   = []         unless defined($features);
	$interfaces = [ 'uefi' ] unless defined($interfaces);

	$info->{'description'}                               = $desc;
	$info->{'interface-types'}                           = $interfaces;
	$info->{'targets'}                                   = [ $target ];
	$info->{'mapping'}->{'device'}                       = 'flash';
	$info->{'mapping'}->{'executable'}->{'format'  }     = 'raw';
	$info->{'mapping'}->{'executable'}->{'filename'}     = $code;
	$info->{'mapping'}->{'nvram-template'}->{'format'}   = 'raw';
	$info->{'mapping'}->{'nvram-template'}->{'filename'} = $vars;
	$info->{'features'}                                  = $features;
	$info->{'tags'}                                      = [ 'git master autobuild' ];

	printf "writing: %s\n", "$file";
	open FILE, ">", $file or die "open $file: $!";
	print FILE $json->pretty->encode($info);
	close FILE;
}

my $info;
my $ia32;
my $ia32smm;
my $x64;
my $x64smm;
my $arm;
my $aa64;

$ia32->{'architecture'} = 'i386';
$ia32->{'machines'} = [ 'pc-i440fx-*', 'pc-q35-*' ];

$ia32smm->{'architecture'} = 'i386';
$ia32smm->{'machines'} = [ 'pc-q35-*' ];

$x64->{'architecture'} = 'x86_64';
$x64->{'machines'} = [ 'pc-i440fx-*', 'pc-q35-*' ];

$x64smm->{'architecture'} = 'x86_64';
$x64smm->{'machines'} = [ 'pc-q35-*' ];

$arm->{'architecture'} = 'arm';
$arm->{'machines'} = [ 'virt-*' ];

$aa64->{'architecture'} = 'aarch64';
$aa64->{'machines'} = [ 'virt-*' ];

# ia32
write_file($dest . "80-ovmf-ia32-git-needs-smm.json",
	   "UEFI Firmware, supports secure boot (git, ia32)",
	   $ia32smm,
	   $base . "ovmf-ia32/OVMF_CODE-needs-smm.fd",
	   $base . "ovmf-ia32/OVMF_VARS-needs-smm.fd",
	   [ 'acpi-s3', 'requires-smm', 'secure-boot' ]);

write_file($dest . "81-ovmf-ia32-git-pure-efi.json",
	   "UEFI Firmware (git, ia32)",
	   $x64,
	   $base . "ovmf-ia32/OVMF_CODE-pure-efi.fd",
	   $base . "ovmf-ia32/OVMF_VARS-pure-efi.fd",
	   [ 'acpi-s3' ]);

write_file($dest . "82-ovmf-ia32-git-with-csm.json",
	   "UEFI Firmware, with CSM (git, ia32)",
	   $ia32,
	   $base . "ovmf-ia32/OVMF_CODE-with-csm.fd",
	   $base . "ovmf-ia32/OVMF_VARS-with-csm.fd",
	   [ 'acpi-s3' ],
	   [ 'uefi', 'bios' ]);

# x64
write_file($dest . "80-ovmf-x64-git-needs-smm.json",
	   "UEFI Firmware, supports secure boot (git, x64)",
	   $x64smm,
	   $base . "ovmf-x64/OVMF_CODE-needs-smm.fd",
	   $base . "ovmf-x64/OVMF_VARS-needs-smm.fd",
	   [ 'acpi-s3', 'requires-smm', 'secure-boot' ]);

write_file($dest . "81-ovmf-x64-git-pure-efi.json",
	   "UEFI Firmware (git, x64)",
	   $x64,
	   $base . "ovmf-x64/OVMF_CODE-pure-efi.fd",
	   $base . "ovmf-x64/OVMF_VARS-pure-efi.fd",
	   [ 'acpi-s3' ]);

write_file($dest . "82-ovmf-x64-git-with-csm.json",
	   "UEFI Firmware, with CSM (git, x64)",
	   $x64,
	   $base . "ovmf-x64/OVMF_CODE-with-csm.fd",
	   $base . "ovmf-x64/OVMF_VARS-with-csm.fd",
	   [ 'acpi-s3' ],
	   [ 'uefi', 'bios' ]);

# arm
write_file($dest . "80-uefi-arm-git.json",
	   "UEFI Firmware (git, arm)",
	   $arm,
	   $base . "arm/QEMU_EFI-pflash.raw",
	   $base . "arm/vars-template-pflash.raw");

# a64
write_file($dest . "80-uefi-a64-git.json",
	   "UEFI Firmware (git, a64)",
	   $aa64,
	   $base . "aarch64/QEMU_EFI-pflash.raw",
	   $base . "aarch64/vars-template-pflash.raw");
