mkdir /build && cd /build
wget https://ftp.gnu.org/gnu/binutils/binutils-2.24.tar.bz2
tar xvf binutils-2.24.tar.bz2
cd binutils-2.24
CFLAGS=-Wno-error ./configure --prefix=/build/install
make && make install
