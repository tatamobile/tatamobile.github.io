Title: How to Download iOS IPA Using ipatools
Date: 2025-8-26 11:35:42
Modified: 2025-8-26 11:35:42
Category: Reverse Engineering
Tags: ios,ipa
Slug: how-to-download-ios-ipa-using-ipatools
Figure: palera1n.png

## Install ipatools

```bash
brew install ipatools
```

## Login Apple Account
```bash
ipatools auth
```

## Download latest version
```bash
ipatool download -b com.meituan.imeituan -i 423084029
ipatool download -b com.dianping.dpscope -i 351091731
```

## Get IPA id
```bash
ipatool search "点评"
```

## Get IPA Version List
```bash
ipatool list-versions -i 351091731 -b com.dianping.dpscope
```

## Download specific version
```bash
ipatool download -b com.meituan.imeituan -i 423084029 --external-version-id 870819560
```