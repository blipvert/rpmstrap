Summary: rpmstrap is a tool for bootstrapping a basic RPM-based system.
Name: rpmstrap
Version: 0.5.1
Release: 1
URL: http://hackers.progeny.com/~sam/rpmstrap
Source0: %{name}-%{version}.tar.bz2
License: GPL
Group: Development/Tools
BuildRoot: %{_tmppath}/%{name}-root
Packager:  PrivateRoot.com <support@privateroot.com>

%description
rpmstrap is a tool for bootstrapping a basic RPM-based system. It is inspired by debootstrap, and allows you to build chroots and basic systems from RPM sources.
At present rpmstrap can build basic Fedora Core 2, Fedora Core 3, Fedora Core 4, Yellowdog 4, CentOS 3, CentOS 4, Mandriva and Scientific Linux systems. It also has support for custom RPM-based systems managed by PDK.

%prep
%setup -q

%install
rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT/usr/bin
mkdir -p $RPM_BUILD_ROOT/usr/lib/rpmstrap
mkdir -p $RPM_BUILD_ROOT/usr/lib/rpmstrap/tools
mkdir -p $RPM_BUILD_ROOT/usr/lib/rpmstrap/scripts
mkdir -p $RPM_BUILD_ROOT/usr/share/doc/rpmstrap-%{version}
install rpmstrap $RPM_BUILD_ROOT/usr/bin
install lib/functions $RPM_BUILD_ROOT/usr/lib/rpmstrap
install lib/scripts/* $RPM_BUILD_ROOT/usr/lib/rpmstrap/scripts/.
install tools/* $RPM_BUILD_ROOT/usr/lib/rpmstrap/tools/.
install lib/*.txt $RPM_BUILD_ROOT/usr/share/doc/rpmstrap-%{version}
install LICENSE $RPM_BUILD_ROOT/usr/share/doc/rpmstrap-%{version}
install README $RPM_BUILD_ROOT/usr/share/doc/rpmstrap-%{version}
install TODO $RPM_BUILD_ROOT/usr/share/doc/rpmstrap-%{version}
install CHANGES $RPM_BUILD_ROOT/usr/share/doc/rpmstrap-%{version}

%post
ln -s /usr/lib/rpmstrap/tools/rpm_solver.py /usr/bin/rpm_solver.py
ln -s /usr/lib/rpmstrap/tools/rpm_refiner.py /usr/bin/rpm_refiner.py
ln -s /usr/lib/rpmstrap/tools/rpm_get-arch.py /usr/bin/rpm_get-arch.py

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root)
/usr

%changelog
* Wed Sep 14 2005  Sam Hart <sam@progeny.com>
- Bump to 0.5.1 release
* Thu Sep 8 2005  Jacob Boswell <jacob@privateroot.com>
- Initial build.
