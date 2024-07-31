# sitelib for noarch packages
%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

Name:           python-virtualenv
Version:        15.1.0
Release:        4%{?dist}
Summary:        Tool to create isolated Python environments

Group:          Development/Languages
License:        MIT
URL:            https://pypi.python.org/pypi/virtualenv
Source0:        https://files.pythonhosted.org/packages/source/v/virtualenv/virtualenv-%{version}.tar.gz

# Disable downloading pip, wheel and setuptools from pypi
# automatically when creating a new venv.
# Upstream commit that was reverted:
# https://github.com/pypa/virtualenv/commit/3d7361ff2e31472cb69d00150fbdf5a3c9af2a0d
Patch0: disable-pypi-downloads-on-venv-creation.patch

# Patch for CVE in the bundled urllib3
# CVE-2018-20060 Cross-host redirect does not remove Authorization header allow for credential exposure
# https://bugzilla.redhat.com/show_bug.cgi?id=CVE-2018-20060
Patch1:         CVE-2018-20060.patch

# Patch for CVE in the bundled urllib3
# CVE-2019-11236 CRLF injection due to not encoding the '\r\n' sequence leading to possible attack on internal service
# https://bugzilla.redhat.com/show_bug.cgi?id=CVE-2019-11236
Patch2:         CVE-2019-11236.patch

# Patch for CVE in the bundled requests
# CVE-2018-18074 Redirect from HTTPS to HTTP does not remove Authorization header
# This patch fixes both the CVE
# https://bugzilla.redhat.com/show_bug.cgi?id=1643829
# and the subsequent regression
# https://github.com/psf/requests/pull/4851
Patch3:         CVE-2018-18074.patch

BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildArch:      noarch
BuildRequires:  python2-devel
Requires:       python-setuptools, python2-devel

Provides:       python2-virtualenv = %{version}-%{release}

%if 0%{?fedora}
BuildRequires:  python-sphinx
%endif


%description
virtualenv is a tool to create isolated Python environments. virtualenv
is a successor to workingenv, and an extension of virtual-python. It is
written by Ian Bicking, and sponsored by the Open Planning Project. It is
licensed under an MIT-style permissive license.


%prep
%setup -q -n virtualenv-%{version}
%patch0 -p1
%{__sed} -i -e "1s|#!/usr/bin/env python||" virtualenv.py 

# Patching of bundled libraries
pushd virtualenv_support/
# Extract wheel content
unzip pip-9.0.*-any.whl
pushd pip/_vendor/requests/packages/urllib3/
%patch1 -p1
%patch2 -p1
popd  # out of wheel
pushd pip/_vendor/requests/
%patch3 -p1
popd # out of wheel
# Replace the pip folder in the zip archive (.whl)
zip -r pip-9.0.*-any.whl pip
# Remove unzipped folders
rm -rf pip/ pip-9.0.*.dist-info/
popd  # out of virtualenv_support

%build
# Build code
%{__python} setup.py build

# Build docs on Fedora
%if 0%{?fedora} > 0
%{__python} setup.py build_sphinx
%endif


%install
rm -rf $RPM_BUILD_ROOT
%{__python} setup.py install --skip-build --root $RPM_BUILD_ROOT
rm -f build/sphinx/html/.buildinfo

# The versioned 2.x script was removed from upstream. Add it back.
cp %{buildroot}/%{_bindir}/virtualenv %{buildroot}/%{_bindir}/virtualenv-%{python2_version}
cp %{buildroot}/%{_bindir}/virtualenv %{buildroot}/%{_bindir}/virtualenv-2


%clean
rm -rf $RPM_BUILD_ROOT


%files
%defattr(-,root,root,-)
%doc docs/*rst PKG-INFO AUTHORS.txt LICENSE.txt
# Include sphinx docs on Fedora
%if 0%{?fedora} > 0
%doc build/sphinx/*
%endif
# For noarch packages: sitelib
%{python_sitelib}/*
%attr(755,root,root) %{_bindir}/virtualenv*


%changelog
* Thu Feb 13 2020 Lumír Balhar <lbalhar@redhat.com> - 15.1.0-4
- Bump
Resolves: rhbz#1649153
Resolves: rhbz#1700824
Resolves: rhbz#1643829

* Tue Jan 14 2020 Lumír Balhar <lbalhar@redhat.com> - 15.1.0-3
- Add three new patches for CVEs in bundled urllib3 and requests
CVE-2018-20060, CVE-2019-11236, CVE-2018-18074
Resolves: rhbz#1649153
Resolves: rhbz#1700824
Resolves: rhbz#1643829

* Wed Sep 13 2017 Charalampos Stratakis <cstratak@redhat.com> - 15.1.0-2
- Add back the versioned virtualenv script
Resolves: rhbz#1461154

* Wed Sep 13 2017 Charalampos Stratakis <cstratak@redhat.com> - 15.1.0-1
- Rebase to version 15.1.0
- Disable automatic downloads from pypi on new venv creation
Resolves: rhbz#1461154

* Wed Feb 08 2017 Charalampos Stratakis <cstratak@redhat.com> - 1.10.1-4
- Fix Python 3.4 compatibility
Resolves: rhbz#1411685

* Mon May 09 2016 Tomas Orsava <torsava@redhat.com> - 1.10.1-3
- Added a patch that shows a custom error message when a FILE passed to
  virtualenv to be used as 'home dir' already exists and is NOT a directory.
Resolves: rhbz#1306513

* Fri Dec 27 2013 Daniel Mach <dmach@redhat.com> - 1.10.1-2
- Mass rebuild 2013-12-27

* Tue Aug 20 2013 Robert Kuska <rkuska@redhat.com> - 1.10.1-1
- Update to v1.10.1 to deal with different securiy issue
Resolves: CVE-2013-1633 

* Wed Jul 17 2013 Robert Kuska <rkuska@redhat.com> - 1.9.1-2
- Delete bundled libraries of pip and setuptools

* Tue May 14 2013 Toshio Kuratomi <toshio@fedoraproject.org> - 1.9.1-1
- Update to upstream 1.9.1 because of security issues with the bundled
  python-pip in older releases.  This is just a quick fix until a
  python-virtualenv maintainer can unbundle the python-pip package
  see: https://bugzilla.redhat.com/show_bug.cgi?id=749378

* Thu Feb 14 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.7.2-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_19_Mass_Rebuild

* Tue Aug 14 2012 Steve Milner <me@stevemilner.org> - 1.7.2-1
- Update for upstream bug fixes.
- Added path for versioned binary.
- Patch no longer required.

* Sat Jul 21 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.7.1.2-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Wed Mar 14 2012 Steve 'Ashcrow' Milner <me@stevemilner.org> - 1.7.1.2-1
- Update for upstream bug fixes.
- Added patch for sphinx building

* Sat Jan 14 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.7-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_17_Mass_Rebuild

* Tue Dec 20 2011 Steve 'Ashcrow' Milner <me@stevemilner.org> - 1.7-1
- Update for https://bugzilla.redhat.com/show_bug.cgi?id=769067

* Wed Feb 09 2011 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.5.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_15_Mass_Rebuild

* Sat Oct 16 2010 Steve 'Ashcrow' Milner <me@stevemilner.org> - 1.5.1-1
- Added _weakrefset requirement for Python 2.7.1.
- Add support for PyPy.
- Uses a proper temporary dir when installing environment requirements.
- Add --prompt option to be able to override the default prompt prefix.
- Add fish and csh activate scripts.

* Thu Jul 22 2010 David Malcolm <dmalcolm@redhat.com> - 1.4.8-4
- Rebuilt for https://fedoraproject.org/wiki/Features/Python_2.7/MassRebuild

* Tue Jul  7 2010 Steve 'Ashcrow' Milner <me@stevemilner.org> - 1.4.8-3
- Fixed EPEL installation issue from BZ#611536

* Tue Jun  8 2010 Steve 'Ashcrow' Milner <me@stevemilner.org> - 1.4.8-2
- Only replace the python shebang on the first line (Robert Buchholz)

* Fri Apr 28 2010 Steve 'Ashcrow' Milner <me@stevemilner.org> - 1.4.8-1
- update pip to 0.7
- move regen-docs into bin/
- Fix #31, make activate_this.py work on Windows (use Lib/site-packages)
unset PYTHONHOME envioronment variable -- first step towards fixing the PYTHONHOME issue; see e.g. https://bugs.launchpad.net/virtualenv/+bug/290844
- unset PYTHONHOME in the (Unix) activate script (and reset it in deactivate())
- use the activate.sh in virtualenv.py via running bin/rebuild-script.py
- add warning message if PYTHONHOME is set

* Fri Apr 2 2010 Steve 'Ashcrow' Milner <me@stevemilner.org> - 1.4.6-1
- allow script creation without setuptools
- fix problem with --relocate when bin/ has subdirs (fixes #12)
- Allow more flexible .pth file fixup
- make nt a required module, along with posix. it may not be a builtin module on jython
- don't mess with PEP 302-supplied __file__, from CPython, and merge in a small startup optimization for Jython, from Jython

* Tue Dec 22 2009 Steve 'Ashcrow' Milner <me@stevemilner.org> - 1.4.3-1
- Updated for upstream release.

* Thu Nov 12 2009 Steve 'Ashcrow' Milner <me@stevemilner.org> - 1.4.2-1
- Updated for upstream release.

* Sun Jul 26 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.3.3-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_12_Mass_Rebuild

* Tue Apr 28 2009 Steve 'Ashcrow' Milner <me@stevemilner.org> - 1.3.3-1
- Updated for upstream release.

* Thu Feb 26 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.3.2-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_11_Mass_Rebuild

* Thu Dec 25 2008 Steve 'Ashcrow' Milner <me@stevemilner.org> - 1.3.2-1
- Updated for upstream release.

* Thu Dec 04 2008 Ignacio Vazquez-Abrams <ivazqueznet+rpm@gmail.com> - 1.3.1-4
- Rebuild for Python 2.6

* Mon Dec  1 2008 Steve 'Ashcrow' Milner <me@stevemilner.org> - 1.3.1-3
- Added missing dependencies.

* Sat Nov 29 2008 Ignacio Vazquez-Abrams <ivazqueznet+rpm@gmail.com> - 1.3.1-2
- Rebuild for Python 2.6

* Fri Nov 28 2008 Steve 'Ashcrow' Milner <me@stevemilner.org> - 1.3.1-1
- Updated for upstream release

* Sun Sep 28 2008 Steve 'Ashcrow' Milner <me@stevemilner.org> - 1.3-1
- Updated for upstream release

* Sat Aug 30 2008 Steve 'Ashcrow' Milner <me@stevemilner.org> - 1.2-1
- Updated for upstream release

* Fri Aug 29 2008 Steve 'Ashcrow' Milner <me@stevemilner.org> - 1.1-3
- Updated from review notes

* Thu Aug 28 2008 Steve 'Ashcrow' Milner <me@stevemilner.org> - 1.1-2
- Updated from review notes

* Tue Aug 26 2008 Steve 'Ashcrow' Milner <me@stevemilner.org> - 1.1-1
- Initial Version
