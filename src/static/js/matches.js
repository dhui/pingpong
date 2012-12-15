$(document).ready(function() {
    $("#doubles").change(function() {
        $(".player2").toggle();
    });

    storeValue = function(obj, new_val) {
        obj.data("old_value", obj.val());
        obj.val(new_val);
    };

    restoreValue = function(obj) {
        var old_value = obj.data("old_value");
        if(old_value) {
            obj.val(old_value);
        }
    };

    $("#deuce").change(function(event) {
        $(".deuceWinner").toggle();
        $(".score").toggle();
    });

    $("#newEntry").click(function() {
        var team1Players = [];
        $("#team1 select:visible").each(function() {
            team1Players.push($(this).val());
        });
        var team2Players = [];
        $("#team2 select:visible").each(function() {
            team2Players.push($(this).val());
        });

        var pointsPerGame = $('input[type="radio"][name="pointsPerGame"]:checked').val();
        var deuce = Boolean($("#deuce:checked").val());

        var team1WonDeuce = $('input[name="deuceWinner"]:checked').val() == "team1";
        var team2WonDeuce = !team1WonDeuce;

        data = {deuce: deuce, pointsPerGame: pointsPerGame, teams: [
            {players: team1Players, score: $("#team1Score").val(), errors: $("#team1Errors").val(), wonDeuce: team1WonDeuce},
            {players: team2Players, score: $("#team2Score").val(), errors: $("#team2Errors").val(), wonDeuce: team2WonDeuce},
        ]};

        $.ajax({
            url: "/matches/",
            type: "POST",
            dataType: "json",
            processData: false,
            data: JSON.stringify(data),
        }).success(function(response) {
            location.reload(true);
        }).error(function() {
            alert("Error adding new entry...");
        });

    });
});