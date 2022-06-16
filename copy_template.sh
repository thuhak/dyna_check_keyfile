#!/bin/bash

src_dir=$(basename $1)
dst_dir=$2

mkdir -p $dst_dir
cp ${src_dir}/${src_dir}.key ${dst_dir}/${dst_dir}.key
sed -i "s/$src_dir/$dst_dir/g" $dst_dir/*.key