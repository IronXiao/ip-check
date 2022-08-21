#!/bin/bash
# better-cloudflare-ip
domain='cloudflaremirrors.com'
file='archlinux/iso/latest/archlinux-x86_64.iso'

function multitest(){
    rm -rf multi_tmp.txt data.txt
    ips=$(cat hits.txt | tr -d '\r')
    for ip in $ips
    do
        echo "正在测试$ip ..."
        curl --resolve $domain:443:$ip https://$domain/$file -o /dev/null --connect-timeout 1 --max-time 10 > log.txt 2>&1
        cat log.txt | tr '\r' '\n' | awk '{print $NF}' | sed '1,3d;$d' | grep -v 'k\|M' >> speed.txt
        for i in `cat log.txt | tr '\r' '\n' | awk '{print $NF}' | sed '1,3d;$d' | grep k | sed 's/k//g'`
        do
            k=$i
            k=$[$k*1024]
            echo $k >> speed.txt
        done
        for i in `cat log.txt | tr '\r' '\n' | awk '{print $NF}' | sed '1,3d;$d' | grep M | sed 's/M//g'`
        do
            i=$(echo | awk '{print '$i'*10 }')
            M=$i
            M=$[$M*1024*1024/10]
            echo $M >> speed.txt
        done
        max=0
        for i in `cat speed.txt`
        do
            if [ $i -ge $max ]
            then
                max=$i
            fi
        done
        realbandwidth=$[$max/1024]
        rm -rf log.txt speed.txt
        echo "  $ip 峰值速度 $realbandwidth kB/s"
        if [[ $realbandwidth -gt $speed ]]
        then
        echo "$ip $realbandwidth kB/s" >> multi_tmp.txt
        fi
    done
    if [ -f "multi_tmp.txt" ]
    then
        echo "筛选ip 为:"
        sort -r -n -k 2 -t \  multi_tmp.txt
        sort -r -n -k 2 -t \  multi_tmp.txt > result.txt
        echo "测速完成，请检查result.txt"
    else
        echo "没有筛选到可用ip, 重试... ..."
        test_job
    fi
    rm -rf multi_tmp.txt
}

function download_zips(){
    rm -rf daily.zip
    curl https://codeload.github.com/ip-scanner/cloudflare/zip/refs/heads/daily -o cloudflare-daily.zip --connect-timeout 30 --retry 10
}


function test_job() {
    rm -rf hits.txt
    ./ip_check
    if [ -f "hits.txt" ]
    then
        echo "可用ip 列表生成成功"
        multitest
    else
        echo "生成可用ip 列表失败，重试..."
        test_job
    fi
}


read -p "请设置期望的带宽大小(默认最小1,单位 Mbps):" bandwidth
read -p "是否下载远程ip 文件[y/n]:" re_dl
if [ -z "$bandwidth" ]
then
    bandwidth=1
fi

if [ "$re_dl" == "y" ]
then
    download_zips
fi

speed=$[$bandwidth*128]

test_job
