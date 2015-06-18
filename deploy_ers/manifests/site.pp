node default {
    exec { 'apt-update':
          command => '/usr/bin/apt-get update',
    }

    Exec["apt-update"] -> Package <| |>

    # !!!! python-couchdb has a weird bug with the replicator database
    # !!!! if the daemon fails to start, try getting the latest version of it
    package {['git', 'curl', 'wget', 'tar', 'python-dev', 'python-pip', 'couchdb', 'python-couchdb']:
        ensure   => installed,
        provider => apt,
        before   => [Exec['CouchDB admin account'], Exec['download ers']],
    }

    package {['avahi-autoipd', 'avahi-dbg', 'avahi-dnsconfd', 'avahi-utils', 'avahi-daemon', 'avahi-discover', 'avahi-ui-utils']:
    ensure => installed,
    provider =>apt,
    }

    package{['restkit', 'couchdbkit', 'virtualenv', 'rdflib']:
        ensure   => installed,
        provider => pip,
        require  => Package['python-pip'],
        before   => Exec['start ers'],
    }

    exec{'CouchDB admin account':
        command => 'echo "admin = -pbkdf2-7a4cc99ded3299e01b97258f0d93eab6dfb0d23e,4a2a5b043eb60d06f3d0204939c35f96,10" >> /etc/couchdb/local.ini',
        user    => root,
        before  => Service['couchdb'],
        path    => ['/usr/bin','/usr/sbin','/bin','/sbin'],
    }
    file { 'couchdb file':
        path => "/etc/couchdb/local.ini",
        ensure => file,
    }

    file{'ers etc directory':
        path   => '/etc/ers-node/',
        before => File['ers config'],
        ensure => directory,
    }

    file{ 'ers config':
        path    => '/etc/ers-node/ers-node.ini',
        content => template('ers/ers-config.erb'),
    }

    service { 'couchdb':
        ensure   => running,
        provider => upstart,
        subscribe => File['couchdb file'],
    }

    exec {'download ers':
        command => 'git clone https://github.com/ers-devs/ers-node.git',
        cwd     => '/vagrant',
        before  => Exec['start ers'],
        require => Package['git'],
        onlyif  => "test ! -e /vagrant/ers-node",
        path    => ['/usr/bin','/usr/sbin','/bin','/sbin'],
    }

    exec{'start ers':
        command => 'python /vagrant/ers-node/ers/daemon.py --config /etc/ers-node/ers-node.ini &',
        path    => ['/usr/bin','/usr/sbin','/bin','/sbin'],
    }
}
