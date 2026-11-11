# CMake 入门示例

[返回项目索引](../README.md)

包含两个独立示例，分别演示 CMake 配置选项和多子目录工程。需要 CMake 与 C 编译工具链；多子目录示例链接 `m` 数学库，按 Linux/GCC 环境组织。

## 配置选项示例：simpleGCC

[simpleGCC/CMakeLists.txt](./simpleGCC/CMakeLists.txt) 演示 `option` 和条件分支：

```bash
cmake -S simpleGCC -B simpleGCC/build -DUSE_FEATURE=ON
```

可将 `ON` 改为 `OFF` 观察输出。目录包含 C 源码，但当前 CMake 配置没有声明可执行目标。

## 多子目录工程：simpleProject

在本目录执行：

```bash
cmake -S simpleProject -B simpleProject/build
cmake --build simpleProject/build
./simpleProject/build/test.elf
```

| 路径 | 内容 |
| --- | --- |
| [simpleProject/CMakeLists.txt](./simpleProject/CMakeLists.txt) | 顶层工程、头文件路径、输出目录及子目录组织 |
| [simpleProject/decCov/](./simpleProject/decCov/) | 十进制转换静态库 |
| [simpleProject/hexCov/](./simpleProject/hexCov/) | 十六进制转换静态库及示例程序 |
| [simpleProject/octCov/](./simpleProject/octCov/) | 八进制转换静态库 |
| [simpleProject/src/](./simpleProject/src/) | 链接各转换库的主程序 |

静态库输出到 `simpleProject/libs/`，可执行文件输出到构建目录。顶层配置还保留了交叉编译工具链的注释示例，使用前需按实际工具链修改。
