%if 0%{?rhel} && 0%{?rhel} <= 6
%{!?__python2: %global __python2 /usr/bin/python2}
%{!?python2_sitelib: %global python2_sitelib %(%{__python2} -c "from distutils.sysconfig import get_python_lib;   print(get_python_lib())")}
%{!?python2_sitearch: %global python2_sitearch %(%{__python2} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib(1))")}
%endif

%global _short_name rerest
%global _short_release 1

Name:           re-rest
Version:        0.0.5
Release:        %{_short_release}%{?dist}
Summary:        Simple REST Api for release automation

License:        AGPLv3+
URL:            https://github.com/RHInception/re-rest
Source0:        https://github.com/RHInception/re-rest/archive/%{version}-%{_short_release}.tar.gz

BuildArch:      noarch
BuildRequires:  python2-devel
BuildRequires:  python-setuptools
Requires:       python-flask >= 0.9
Requires:       python-pika >= 0.9.12
Requires:       python-pymongo
Requires:       python-blinker
Requires:       python-ldap
Requires:       PyYAML
Requires:       python-jsonschema


%description
Simple REST Api for release automation.

%check

%prep
%setup -n rerest-%{version}-%{_short_release} -q

%build
%{__python2} setup.py build


%install
rm -rf $RPM_BUILD_ROOT
%{__python2} setup.py install --skip-build --root $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT/%{_datarootdir}/rerest/{mod_wsgi,test-ca-script}/
cp -rf contrib/mod_wsgi/* $RPM_BUILD_ROOT/%{_datarootdir}/rerest/mod_wsgi/


%files
%defattr(-, root, root)
%doc README.md LICENSE AUTHORS
%{python2_sitelib}/*
%{_datarootdir}/rerest/*


%changelog
* Tue Jun 24 2014 Steve Milner <stevem@gnulinux.net> - 0.0.5-1
- id no longer being set when GETing a playbook.

* Mon Jun 23 2014 Tim Bielawa <tbielawa@redhat.com> - 0.0.4-3
- Fix typo

* Wed Jun 18 2014 Steve Milner <stevem@gnulinux.net> - 0.0.4-2
- Defattr not being used in files section.

* Thu Jun  5 2014 Chris Murphy <chmurphy@redhat.com> - 0.0.4-1
- Refacter for easier building

* Thu Jun  5 2014 Chris Murphy <chmurphy@redhat.com> - 0.0.3-3
- Refacter for easier building

* Mon May 19 2014 Steve Milner <stevem@gnulinux.net> - 0.0.3-2
- python-jsonschema added.

* Mon May 19 2014 Steve Milner <stevem@gnulinux.net> - 0.0.3-1
- PyYAML is now needed.

* Thu May  1 2014 Steve Milner <stevem@gnulinux.net> - 0.0.2-1
- Mongo support.

* Tue Apr  8 2014 Steve Milner <stevem@gnulinux.net> - 0.0.1-1
- Initial spec
