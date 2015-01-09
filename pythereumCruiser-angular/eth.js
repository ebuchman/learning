
var myApp = angular.module('myApp',[]);                                               
                                                                                      
myApp.controller("EthCtrl", ['$scope', '$http', function($scope, $http){

    $scope.apicall = '';

    $scope.getBlocks = function() {
      $scope.apicall = 'blocks/';  
      $scope.httpReq();
    };

    $scope.getBlock = function() {
      $scope.apicall = 'blocks/'+this.block_hash_text;
      $scope.httpReq();

    };

    $scope.getConnectedPeers = function() {
      $scope.apicall = 'connected_peers/';
      $scope.httpReq();
    };

    $scope.getKnownPeers = function() {
      $scope.apicall = 'known_peers/';
      $scope.httpReq();
    };

    $scope.httpReq = function() {
        $scope.path = 'http://localhost:30203/api/v0alpha/'+$scope.apicall;

        $http.get($scope.path).                      
            then(function(data) {
                $scope.ret = data;
            }, function(err) { $scope.error = 'Oh no! An error!'});
    }

}]);                                                                                   

