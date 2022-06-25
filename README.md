# LS-Dyna keyfile utils

## check_keyfile.py

检查ls-dyna keyfile中include 引用的.k, .i, .k.asc文件， 查询xx_数字模式的文件，搜索这些文件是否有更新的版本。
并可以做一键更新

### 使用前安装

```bash
python3.6 -m pip install -r requirements.txt
```

### 使用举例

#### 检查文件是否有更新，如果有更新会提示是否更新

```bash
./check_keyfile.py test_run_001.key
```

#### 只检查keyfile，不提示，直接更新

```bash
./check_keyfile.py  test_run_001.key --u yes
```

#### 批量搜索当前目录之下所有的keyfile是否有更新，不直接更新

```bash
find -name '*.key' | xargs ./check_keyfile.py -u no
```

### 其他注意事项

- 需要避免keyfile出现文件名字相同，但是目录不一样的情况，否则会一起替换

## export_keyfile.py

将dyna中include的key导出

### 使用举例

##### 将当前文件夹下面所有的.key文件导出到/tmp/dyna目录

```bash
./export_keyfile.py -o /tmp/dyna *.key
```








