# BD-Plugin

構成:
    BDGinie:使用Docker封裝的主程式API，放置在ACR上面運行，讓source.py來打
    (需要獨立出來是因為它需要的第三方包Pyodide不支援)

    達哥插件包:使用source.py的pyfetch來打BDGinie API，然後自己再做為一隻API