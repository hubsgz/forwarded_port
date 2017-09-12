# forwarded_port
python端口转发工具， 支持tpc和udp

用法:

udp端口转发:
myp=portmapUDP(53,'192.168.0.206',53)
myp.start()

tcp端口转发:
myp=portmap(80,'192.168.0.206',80)
myp.start()
