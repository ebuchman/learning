package main

import (
    "log"
    "net"
    "fmt"
    "flag"
    "os"
    "bufio"
)

var (
    listen_port = flag.String("listen_port", "3333", "listen port")
    remote_host = flag.String("remote_host", "localhost", "remote host")
    remote_port = flag.String("remote_port", "3334", "remote port")
)

// listen on port. Accept connections.  Broadcast new connection on peer_channel (dealt with by PeerManager)
func listenServer(ch chan net.Conn){
    ln, err := net.Listen("tcp", ":"+*listen_port)
    if err != nil{
        log.Fatal(err)
    } else {
        log.Println("listening on ", *listen_port)
    }
    for {
        conn, err := ln.Accept()
        fmt.Println(conn)
        if err!= nil{
            continue
        }
        ch <- conn
    }
}

// read new input from std in.  Broadcast on stdin_channel
func stdInput(ch chan string){
    bio := bufio.NewReader(os.Stdin)
    for {
        bytes, _, err := bio.ReadLine()
        if err != nil{
           fmt.Println("stdin read error") 
           break
        }
        ch <- string(bytes)
    }
}

// Each peer has its own channel to get msgs that should be written out to that peer
type Peer struct{
    nick string
    addr string
    conn net.Conn
    ch chan []byte
    quit bool
}

func readPeer(me *Peer, quit_ch chan Peer){
    buf := make([]byte, 1024)
    con := (*me).conn
    // read loop - try and read over socket, print result to terminal
    for{
        n, err := con.Read(buf)
        if err != nil || n == 0{
            (*me).quit = true
            quit_ch <- *me
            break
        }
        fmt.Println(con.RemoteAddr().String() + ": " + string(buf[:n]))
    }
}

func writePeer(me *Peer, quit_ch chan Peer){
    con := me.conn
    // write loop.  If something comes in on me.ch, write msg to peer
    for {
        buf := <- (*me).ch   
        n, err := con.Write(buf)
        if err!=nil || n == 0{
            (*me).quit = true
            quit_ch <- *me
            break
        }
    }
}

// each peer has a PeerLoop with two concurrent funcs, one for reading, one for writing.
func peerLoop(me Peer, quit_ch chan Peer){
    go readPeer(&me, quit_ch)
    go writePeer(&me, quit_ch)
}

// connect to peers from command line args.
// this should expand to read known peers from a file
func connectPeers(peers map[string]Peer, quit_ch chan Peer){
   conn, err := net.Dial("tcp", *remote_host + ":" + *remote_port)
   if err != nil{
        fmt.Println(err)   
   }else{
       this_peer := Peer{"jim", conn.RemoteAddr().String(), conn, make(chan []byte), false}
       peers[this_peer.addr] = this_peer
       go peerLoop(this_peer, quit_ch)
   }
}

// When a new peer connects, create Peer and add to peers
func addNewPeer(peers *map[string]Peer, con net.Conn) Peer{
    fmt.Println("New Peer!", con.RemoteAddr())
    this_peer := Peer{"bob", con.RemoteAddr().String(), con, make(chan []byte), false}
    (*peers)[con.RemoteAddr().String()] = this_peer
    return this_peer
}

// close a peer connection and remove from peers
func closePeer(peers *map[string]Peer, peer *Peer){
    addr := (*peer).addr
    (*peers)[addr].conn.Close()
    delete((*peers), addr)
    fmt.Println("closing peer", *peer)
}

// send a message to all peers by writing to their channels
func broadcastMsg(peers map[string]Peer, msg string){
    for _, p := range peers{
        //fmt.Println("sending  to ", p.addr, "this msg", msg)
        p.ch <- []byte(msg)
    }
}

// manage peers: 1) accept new peers. 2) broadcast new writes. 3) broadcast new std inputs
func peerManager(peer_ch chan net.Conn, quit_ch chan Peer, stdin_ch chan string){
    peers := make(map[string]Peer) // map from ip to Peer
    connectPeers(peers, quit_ch)
    for {
        select{
        case new_peer := <- peer_ch:
            if new_peer != nil{
                this_peer := addNewPeer(&peers, new_peer)
                go peerLoop(this_peer, quit_ch)
            }
        case to_quit := <- quit_ch:
           closePeer(&peers, &to_quit)
        case input := <- stdin_ch:
           broadcastMsg(peers, input) 
        }
    }
}

func main(){
    flag.Parse()

    peer_ch := make(chan net.Conn) // for serving new peers from the tcpServer
    defer close(peer_ch)
    quit_ch := make(chan Peer) // signal to close a peer
    defer close(quit_ch)
    stdin_ch := make(chan string) // input from stdin
    defer close(stdin_ch)

    go listenServer(peer_ch)
    go stdInput(stdin_ch)
    peerManager(peer_ch, quit_ch, stdin_ch)
}

