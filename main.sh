#!/bin/bash
# better-cloudflare-ip

function multitest(){
    rm -rf multi_tmp.txt data.txt
    ips=$(cat hits.txt | tr -d '\r')
    for ip in $ips
    do
        rm -rf data.txt
        echo "resolve host by $ip ..."
        curl --ipv4 --resolve service.baipiaocf.ml:443:$ip --retry 1 https://service.baipiaocf.ml -o data.txt -# --connect-timeout 2 --max-time 3
        if [ $? -eq 0 -a -f "data.txt" ]
        then
            break
        fi
    done
    domain=$(grep domain= data.txt | cut -f 2- -d'=')
    file=$(grep file= data.txt | cut -f 2- -d'=')
    rm -rf data.txt
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
    else
        echo "没有筛选到可用ip"
    fi
    rm -rf multi_tmp.txt
}

function download_zips(){
    rm -rf daily.zip
    curl https://codeload.github.com/ip-scanner/cloudflare/zip/refs/heads/daily -o cloudflare-daily.zip --connect-timeout 30 --retry 10
}


read -p "请设置期望的带宽大小(默认最小1,单位 Mbps):" bandwidth
if [ -z "$bandwidth" ]
then
    bandwidth=1
fi
speed=$[$bandwidth*128]


download_zips
./ip_check
multitest
echo "批量测速已完成，请检查result.txt"
