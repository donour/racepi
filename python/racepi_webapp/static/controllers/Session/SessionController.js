"use strict";
app.controller('sessionCtrl', function($scope, $http) {
    $http.get("/sessions")
    .then(function (response) {$scope.sessions = response.data.result;});
});