// general framework for ajax calls.
function new_request_obj(){
    if (window.XMLHttpRequest)
        return new XMLHttpRequest();
    else
        return new ActiveXObject("Microsoft.XMLHTTP");
}

function register_callback(xmlhttp, _func, args){
    xmlhttp.onreadystatechange=function(){
        if (xmlhttp.readyState==4 && xmlhttp.status==200){
            args.unshift(xmlhttp);
            _func.apply(this, args);
        }
    }
}

function make_request(xmlhttp, method, path, async, params){
    xmlhttp.open(method, path, async);
    xmlhttp.setRequestHeader("Content-type", "application/json");
    //xmlhttp.setRequestHeader("Content-length", s.length); // important?
    xmlhttp.send(JSON.stringify(params));
}

function compile_callback(xmlhttp){
    console.log("response:", xmlhttp.responseText);
    response = JSON.parse(xmlhttp.responseText);
    console.log(response);
    document.getElementById("bytecode").innerHTML = "Compiled bytecode: 0x"+xmlhttp.responseText;
    console.log('done');
}

function compile(){
    code = document.getElementById("code").value;
    console.log("hi nikki");
    console.log("the user entered:", code)
    xmlhttp = new_request_obj();
    register_callback(xmlhttp, compile_callback, []);
    make_request(xmlhttp, "GET", "/request.php?stuff="+code, true, {}); // {"scripts":c});
    return false;
}

