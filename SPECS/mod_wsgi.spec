%define _trivial .0
%define _buildid .3

%{!?_httpd_apxs: %{expand: %%global _httpd_apxs %%{_sbindir}/apxs}}
%{!?_httpd_mmn: %{expand: %%global _httpd_mmn %%(cat %{_includedir}/httpd/.mmn || echo missing-httpd-devel)}}
%{!?_httpd_confdir:    %{expand: %%global _httpd_confdir    %%{_sysconfdir}/httpd/conf.d}}
# /etc/httpd/conf.d with httpd < 2.4 and defined as /etc/httpd/conf.modules.d with httpd >= 2.4
%{!?_httpd_modconfdir: %{expand: %%global _httpd_modconfdir %%{_sysconfdir}/httpd/conf.d}}
%{!?_httpd_moddir:    %{expand: %%global _httpd_moddir    %%{_libdir}/httpd/modules}}

#Amazon condition to build with both python 2 and 3 sub-packages
%if 0%{?amzn2}
%global with_python3 1
%global with_python2 1
%endif

Name:           mod_wsgi
Version:        3.4
Release:        12%{?dist}%{?_trivial}%{?_buildid}
Summary:        A WSGI interface for Python web applications in Apache
Group:          System Environment/Libraries
License:        ASL 2.0
URL:            http://modwsgi.org
Source0:        http://modwsgi.googlecode.com/files/%{name}-%{version}.tar.gz
Source1:        wsgi.conf
Source2:        wsgi-python3.conf
Patch0:         mod_wsgi-3.4-connsbh.patch
Patch1:         mod_wsgi-3.4-procexit.patch
Patch2:         mod_wsgi-3.4-coredump.patch
Patch3:         mod_wsgi-3.4-CVE-2014-0240.patch
Patch100:       CVE-2014-8583.patch
Patch101:       mod_wsgi-3.4-python.patch
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildRequires:  httpd-devel, autoconf, gcc
#Requires: httpd-mmn = %{_httpd_mmn}

# Suppress auto-provides for module DSO
%{?filter_provides_in: %filter_provides_in %{_httpd_moddir}/.*\.so$}
%{?filter_setup}

%global _description\
The mod_wsgi adapter is an Apache module that provides a WSGI compliant\
interface for hosting Python based web applications within Apache. The\
adapter is written completely in C code against the Apache C runtime and\
for hosting WSGI applications within Apache has a lower overhead than using\
existing WSGI adapters for mod_python or CGI.\

%description %_description

%if 0%{?with_python2} > 0
%package -n python2-%{name}
Summary: %summary
Requires:       httpd-mmn = %{_httpd_mmn}
BuildRequires:  python2-devel, python2-setuptools
%{?python_provide:%python_provide python2-%{name}}
#Remove before F30
Provides: mod_wsgi = %{version}-%{release}
Provides: mod_wsgi%{?_isa} = %{version}-%{release}
Obsoletes: mod_wsgi < %{version}-%{release}

%description -n python2-%{name} %_description
%endif

%if 0%{?with_python3} > 0
%package -n python3-%{name}
Summary:        %summary
Requires:       httpd-mmn = %{_httpd_mmn}
BuildRequires:  python3-devel, python3-sphinx

%if 0%{?with_python2} == 0
Provides: mod_wsgi = %{version}-%{release}
Provides: mod_wsgi%{?_isa} = %{version}-%{release}
Obsoletes: mod_wsgi < %{version}-%{release}
%endif

%description -n python3-%{name} %_description
%endif

%prep
%setup -q

%autosetup -p1 -n %{name}-%{version}
 
: Python2=%{with_python2} Python3=%{with_python3}

%build
# Regenerate configure for -coredump patch change to configure.in
autoconf
export LDFLAGS="$RPM_LD_FLAGS -L%{_libdir}"
export CFLAGS="$RPM_OPT_FLAGS -fno-strict-aliasing"

%if 0%{?with_python3} > 0
mkdir py3build/
# this always produces an error (because of trying to copy py3build
# into itself) but we don't mind, so || :
cp -R * py3build/ || :
pushd py3build
%configure --enable-shared --with-apxs=%{_httpd_apxs} --with-python=python3
%{make_build}
popd
%endif

%if 0%{?with_python2} > 0
%configure --enable-shared --with-apxs=%{_httpd_apxs} --with-python=python2
%{make_build}
%endif

%install
# first install python3 variant and rename the so file
%if 0%{?with_python3} > 0
pushd py3build
make install DESTDIR=$RPM_BUILD_ROOT LIBEXECDIR=%{_httpd_moddir}
mv  $RPM_BUILD_ROOT%{_httpd_moddir}/mod_wsgi{,_python3}.so
 
install -d -m 755 $RPM_BUILD_ROOT%{_httpd_modconfdir}
# httpd >= 2.4.x
install -p -m 644 %{SOURCE2} $RPM_BUILD_ROOT%{_httpd_modconfdir}/10-wsgi-python3.conf
 
popd
 
%endif

# second install python2 variant
%if 0%{?with_python2} > 0
make install DESTDIR=$RPM_BUILD_ROOT LIBEXECDIR=%{_httpd_moddir}
 
install -d -m 755 $RPM_BUILD_ROOT%{_httpd_modconfdir}
# httpd >= 2.4.x
install -p -m 644 %{SOURCE1} $RPM_BUILD_ROOT%{_httpd_modconfdir}/10-wsgi.conf
 
%endif
 
%clean
rm -rf $RPM_BUILD_ROOT
 
%if 0%{?with_python2} > 0
%files -n python2-%{name}
%doc LICENCE README
%config(noreplace) %{_httpd_modconfdir}/*wsgi.conf
%{_httpd_moddir}/mod_wsgi.so
%endif

%if 0%{?with_python3} > 0
%files -n python3-%{name}
%doc LICENCE README
%config(noreplace) %{_httpd_modconfdir}/*wsgi-python3.conf
%{_httpd_moddir}/mod_wsgi_python3.so
%endif

%changelog
* Mon Apr 12 2021 Sonia Xu <sonix@amazon.com> - 3.4-12.amzn2.0.3
- Add amzn2 conditions and patch to build for python3

* Tue Aug 19 2014 Jan Kaluza <jkaluza@redhat.com> - 3.4-12
- fix possible privilege escalation in setuid() (CVE-2014-0240)

* Fri Jan 24 2014 Daniel Mach <dmach@redhat.com> - 3.4-11
- Mass rebuild 2014-01-24

* Mon Jan 13 2014 Joe Orton <jorton@redhat.com> - 3.4-10
- rebuild for #1029360

* Fri Dec 27 2013 Daniel Mach <dmach@redhat.com> - 3.4-9
- Mass rebuild 2013-12-27

* Thu Feb 14 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 3.4-8
- Rebuilt for https://fedoraproject.org/wiki/Fedora_19_Mass_Rebuild

* Tue Dec 11 2012 Jan Kaluza <jkaluza@redhat.com> - 3.4-7
- compile with -fno-strict-aliasing to workaround Python
  bug http://www.python.org/dev/peps/pep-3123/

* Thu Nov 22 2012 Joe Orton <jorton@redhat.com> - 3.4-6
- use _httpd_moddir macro

* Thu Nov 22 2012 Joe Orton <jorton@redhat.com> - 3.4-5
- spec file cleanups

* Wed Oct 17 2012 Joe Orton <jorton@redhat.com> - 3.4-4
- enable PR_SET_DUMPABLE in daemon process to enable core dumps

* Wed Oct 17 2012 Joe Orton <jorton@redhat.com> - 3.4-3
- use a NULL c->sbh pointer with httpd 2.4 (possible fix for #867276)
- add logging for unexpected daemon process loss

* Wed Oct 17 2012 Matthias Runge <mrunge@redhat.com> - 3.4-2
- also use RPM_LD_FLAGS for build bz. #867137

* Mon Oct 15 2012 Matthias Runge <mrunge@redhat.com> - 3.4-1
- update to upstream release 3.4

* Fri Jul 20 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 3.3-7
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Wed Jun 13 2012 Joe Orton <jorton@redhat.com> - 3.3-6
- add possible fix for daemon mode crash (#831701)

* Mon Mar 26 2012 Joe Orton <jorton@redhat.com> - 3.3-5
- move wsgi.conf to conf.modules.d

* Mon Mar 26 2012 Joe Orton <jorton@redhat.com> - 3.3-4
- rebuild for httpd 2.4

* Tue Mar 13 2012 Joe Orton <jorton@redhat.com> - 3.3-3
- prepare for httpd 2.4.x

* Fri Jan 13 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 3.3-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_17_Mass_Rebuild

* Tue Nov 01 2011 James Bowes <jbowes@redhat.com> 3.3-1
- update to 3.3

* Tue Feb 08 2011 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 3.2-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_15_Mass_Rebuild

* Tue Jul 27 2010 David Malcolm <dmalcolm@redhat.com> - 3.2-2
- Rebuilt for https://fedoraproject.org/wiki/Features/Python_2.7/MassRebuild

* Tue Mar  9 2010 Josh Kayse <joshkayse@fedoraproject.org> - 3.2-1
- update to 3.2

* Sun Mar 07 2010 Josh Kayse <joshkayse@fedoraproject.org> - 3.1-2
- removed conflicts as it violates fedora packaging policy

* Sun Mar 07 2010 Josh Kayse <joshkayse@fedoraproject.org> - 3.1-1
- update to 3.1
- add explicit enable-shared
- add conflicts mod_python < 3.3.1

* Sat Jul 25 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.5-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_12_Mass_Rebuild

* Thu Jul 02 2009 James Bowes <jbowes@redhat.com> 2.5-1
- Update to 2.5

* Wed Feb 25 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.3-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_11_Mass_Rebuild

* Sun Nov 30 2008 Ignacio Vazquez-Abrams <ivazqueznet+rpm@gmail.com> - 2.3-2
- Rebuild for Python 2.6

* Tue Oct 28 2008 Luke Macken <lmacken@redhat.com> 2.3-1
- Update to 2.3

* Mon Sep 29 2008 James Bowes <jbowes@redhat.com> 2.1-2
- Remove requires on httpd-devel

* Wed Jul 02 2008 James Bowes <jbowes@redhat.com> 2.1-1
- Update to 2.1

* Mon Jun 16 2008 Ricky Zhou <ricky@fedoraproject.org> 1.3-4
- Build against the shared python lib.

* Tue Feb 19 2008 Fedora Release Engineering <rel-eng@fedoraproject.org> - 1.3-3
- Autorebuild for GCC 4.3

* Sun Jan 06 2008 James Bowes <jbowes@redhat.com> 1.3-2
- Require httpd

* Sat Jan 05 2008 James Bowes <jbowes@redhat.com> 1.3-1
- Update to 1.3

* Sun Sep 30 2007 James Bowes <jbowes@redhat.com> 1.0-1
- Initial packaging for Fedora

