For webrtc, a request like this is reasonable

Answer sdp:  v=0
OWN:
VideoTester.vue:107 {"type":"offer","sdp":"v=0
o=- 5876172445819097706 2 IN IP4 127.0.0.1
s=-
t=0 0
a=group:BUNDLE 0
a=extmap-allow-mixed
a=msid-semantic: WMS
m=application 41690 UDP/DTLS/SCTP webrtc-datachannel
c=IN IP4 104.30.148.159
a=candidate:174105576 1 udp 2113937151 370df942-aa3e-431a-a2b0-b1af411bdf46.local 62747 typ host generation 0 network-cost 999
a=candidate:1332518358 1 udp 1677729535 82.57.76.116 62747 typ srflx raddr 0.0.0.0 rport 0 generation 0 network-cost 999
a=candidate:790156930 1 udp 33563135 104.30.148.159 41690 typ relay raddr 82.57.76.116 rport 62747 generation 0 network-cost 999
a=candidate:1870377041 1 udp 33563903 104.30.148.153 25859 typ relay raddr 82.57.76.116 rport 62747 generation 0 network-cost 999
a=candidate:3850816556 1 udp 16785663 104.30.149.171 36743 typ relay raddr 82.57.76.116 rport 55197 generation 0 network-cost 999
a=candidate:4138333278 1 udp 16786431 104.30.148.152 18863 typ relay raddr 82.57.76.116 rport 55195 generation 0 network-cost 999
a=candidate:3850816556 1 udp 16785663 104.30.149.171 65451 typ relay raddr 82.57.76.116 rport 55201 generation 0 network-cost 999
a=candidate:3634104051 1 udp 8191 104.30.148.157 48785 typ relay raddr 82.57.76.116 rport 55198 generation 0 network-cost 999
a=candidate:3033795292 1 udp 16786431 104.30.149.167 64422 typ relay raddr 82.57.76.116 rport 55199 generation 0 network-cost 999
a=candidate:1109558103 1 udp 8959 104.30.149.165 15356 typ relay raddr 82.57.76.116 rport 55196 generation 0 network-cost 999
a=candidate:2874972317 1 udp 8191 104.30.150.85 59313 typ relay raddr 82.57.76.116 rport 55202 generation 0 network-cost 999
a=candidate:2113691366 1 udp 8959 104.30.149.163 37531 typ relay raddr 82.57.76.116 rport 55200 generation 0 network-cost 999
a=ice-ufrag:Jt9i
a=ice-pwd:8zDs4Lljigvr6NdzrWz5z3Kd
a=ice-options:trickle
a=fingerprint:sha-256 55:85:29:EF:F4:33:5B:48:1F:87:3C:61:9A:02:E1:2E:54:D9:B4:D0:6E:75:74:EB:6F:B2:90:92:6E:66:1F:CD
a=setup:actpass
a=mid:0
a=sctp-port:5000
a=max-message-size:262144
"}

SERVER:
{"sdp":"v=0
o=- 3964494337 3964494337 IN IP4 0.0.0.0
s=-
t=0 0
a=group:BUNDLE 0
a=msid-semantic:WMS *
m=application 41011 UDP/DTLS/SCTP webrtc-datachannel
c=IN IP4 172.18.0.6
a=mid:0
a=sctp-port:5000
a=max-message-size:65536
a=candidate:9303288ef12d43e9a6fb97e5a5af29f6 1 udp 2130706431 172.18.0.6 41011 typ host
a=candidate:8ce0e1e4140f511df1806b446265f825 1 udp 1694498815 82.57.76.116 56519 typ srflx raddr 172.18.0.6 rport 41011
a=end-of-candidates
a=ice-ufrag:GbDK
a=ice-pwd:T3Fu9H8wq4vntvOeYllGCf
a=fingerprint:sha-256 70:97:D0:BA:9B:3E:1D:92:9D:AC:F0:EF:54:52:39:CF:5D:89:14:F2:91:BE:57:E8:B3:05:94:91:73:DE:98:DC
a=fingerprint:sha-384 BE:31:E9:3D:6C:C2:8B:56:06:B8:95:1B:33:56:1C:32:90:2F:55:2D:86:B7:07:D2:A3:9E:71:D5:B9:AD:5B:EE:08:6D:C2:1E:A3:4B:D3:6E:7B:DF:1B:FE:97:0A:4B:8E
a=fingerprint:sha-512 55:19:BC:8E:A4:B0:BD:87:0A:83:A7:BD:E7:E4:35:1A:7D:38:9B:AA:D1:77:53:20:8F:50:EE:82:EB:5C:7D:6E:8C:1B:B6:19:23:56:4C:A8:03:B3:B0:24:7E:C7:98:61:6A:B6:7D:7B:DF:42:92:E5:1C:66:96:72:BB:E4:B3:04
a=setup:active
","type":"answer"}


You always need ice candidates for both client and server.