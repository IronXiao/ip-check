chcp 65001 > nul
@echo off
cd "%~dp0"
setlocal enabledelayedexpansion

cls
:main
title CF优选IP

:bettercloudflareip
set /a hit=0
set /a bandwidth=1
set /p bandwidth=请设置期望的带宽大小(默认最小%bandwidth%,单位 Mbps):
set re_dl=n
set /p re_dl=请设置是否下载远程ip 列表文件[y/n](默认为%re_dl%):
if %bandwidth% EQU 0 (set /a bandwidth=1)
set /a speed=bandwidth*128
call :start
exit


:start
if !re_dl! == y (
curl https://codeload.github.com/ip-scanner/cloudflare/zip/refs/heads/daily -o cloudflare-daily.zip --connect-timeout 30 --retry 10
)
:redo
del hits.txt > nul 2>&1
ip_check.exe
if exist hits.txt (
echo 成功找到可用ip！
) else (
echo 没有找到可用ip, 重试... ...
goto redo
)

set domain=cloudflaremirrors.com
set file=archlinux/iso/latest/archlinux-x86_64.iso
title 启动测速
del result.txt > nul 2>&1

for /f "delims=" %%i in (hits.txt) do (
del CRLF.txt cut.txt speed.txt > nul 2>&1
set anycast=%%i
echo 正在测试 !anycast!
curl --resolve !domain!:443:!anycast! https://!domain!/!file! -o nul --connect-timeout 1 --max-time 10 > CR.txt 2>&1
findstr "0:" CR.txt >> CRLF.txt
CR2CRLF.exe CRLF.txt > nul
for /f "delims=" %%i in (CRLF.txt) do (
set s=%%i
set s=!s:~73,5!
echo !s%! >> cut.txt
)
for /f "delims=" %%i in ('findstr /v "k M" cut.txt') do (
set x=%%i
set x=!x:~0,5!
set /a x=!x%!/1024
echo !x! >> speed.txt
)
for /f "delims=" %%i in ('findstr "k" cut.txt') do (
set x=%%i
set x=!x:~0,4!
set /a x=!x%!
echo !x! >> speed.txt
)
for /f "delims=" %%i in ('findstr "M" cut.txt') do (
set x=%%i
set x=!x:~0,2!
set y=%%i
set y=!y:~3,1!
set /a x=!x%!*1024
set /a y=!y%!*1024/10
set /a z=x+y
echo !z! >> speed.txt
)
set /a max=0
for /f "tokens=1,2" %%i in ('type "speed.txt"') do (
if %%i GEQ !max! set /a max=%%i
)
echo !anycast! 峰值速度 !max! kB/s
if !max! GEQ !speed! (
echo !anycast!: !max! kB/s>> result.txt
set /a hit=!hit!+1
)
)
del rtt.txt data.txt CR.txt CRLF.txt cut.txt speed.txt meta.txt > nul 2>&1
RD /S /Q rtt > nul 2>&1
if !hit! GEQ 1 (
echo 筛选到可用ip：
for /f "delims=" %%i in (result.txt) do (
echo %%i
)
) else (
echo 没有筛选到可用ip，重试... ...
goto redo
)
pause > nul
goto :eof
