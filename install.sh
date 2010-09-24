#!/bin/sh

VERSION=0.5.2

if [ "$BINDIR" = "" ]; then
    BINDIR=$DESTDIR/usr/bin
fi

if [ "$LIBDIR" = "" ]; then
    LIBDIR=$DESTDIR/usr/lib/rpmstrap
fi

if [ "$DOCDIR" = "" ]; then
    DOCDIR=/$DESTDIR/usr/share/doc
fi
DOCDIR=$DOCDIR/rpmstrap-$VERSION

# Define the tools to install
TOOLS=$(cat <<EOF
rpm_solver.py
rpm_refiner.py
rpm_get-arch.py
rpm_get-update.py
rpmdiff.py
rpm_migrate.sh
compstool.py
progress_bar.py
rpmdiff_lib.py
suite_upgrader.py
EOF
)

if [ $# != 0 ] ; then
    while true ; do
        case "$1" in
            -h)
                echo "install.sh"
                echo "----------"
                echo "Run with no arguments to install software"
                echo "Run with '-p' to purge/remove old software"
                exit 0
                ;;
            -p)
                rm -f $BINDIR/rpmstrap
                for a in $TOOLS
                do
                    rm -f $BINDIR/$a
                done
                rm -fr $LIBDIR
                rm -fr $DOCDIR
                echo "rpmstrap purged"
                exit 0
                ;;
            *)
                break
                ;;
        esac
    done
fi

# Default is to install

mkdir -p $BINDIR
cp -fr rpmstrap $BINDIR/.
chmod a+x $BINDIR/rpmstrap
mkdir -p $LIBDIR
cp -fr lib/functions $LIBDIR/.
cp -fr lib/scripts $LIBDIR/.
cp -fr tools/ $LIBDIR/.
for a in $TOOLS
do
    ln -s $LIBDIR/tools/$a $BINDIR/$a
    chmod a+x $BINDIR/$a
done
mkdir -p $DOCDIR
cp -fr lib/*.txt $DOCDIR/.
cp -fr LICENSE $DOCDIR/.
cp -fr README $DOCDIR/.
cp -fr tools/README $DOCDIR/README.tools
cp -fr TODO $DOCDIR/.
cp -fr CHANGES $DOCDIR/.

echo rpmstrap installed
