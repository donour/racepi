"use strict";
app.controller('tableDataController', function($scope, $http) {
    $http.get("/gps")
    .then(function (response) {$scope.gpsSamples = response.data.result;});
});