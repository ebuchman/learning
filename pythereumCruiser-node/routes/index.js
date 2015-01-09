var express = require('express');
var router = express.Router();
var http = require('http');


router.get('/', function(req, res) {
  var path_call = '';

  if (Object.keys(req.query).length > 0 ){
      if (req.query['blocks'])
        path_call = 'blocks/';
      else if (req.query['block_hash'])
        path_call = 'blocks/'+req.query['block_hash'];
      else if (req.query['connected_peers'])
        path_call = 'connected_peers/';
      else if (req.query['known_peers'])
        path_call = 'known_peers/';
      else
        console.log('unknown api call (check slashes!)');


      var optionsget ={
          host: 'localhost',
          port: '30203',
          method: 'GET',
          path: '/api/v1/'+path_call
      };

      callback = function(response) {
          var str='';
          response.on('data', function (chunk) {
              str+=chunk;
          });
      
          response.on('end', function() {
              res.render('index', { title: 'Express', api_results:str, available_api_calls: ['blocks'] });
          });
      }
      
      var req = http.request(optionsget, callback);
      req.end()
  }
  else
    res.render('index', { title: 'Express',  available_api_calls: ['blocks'] });

});


module.exports = router;
