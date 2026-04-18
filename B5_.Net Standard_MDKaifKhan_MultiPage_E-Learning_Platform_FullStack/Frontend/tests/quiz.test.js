const {calculateGrade}=require("../js/quiz");

test("grade calculation",()=>{

expect(calculateGrade(95)).toBe("A");

});

test("percentage calculation",()=>{

const score=4;
const total=5;

expect((score/total)*100).toBe(80);

});

test("pass fail logic",()=>{

function passFail(percent){
return percent>=50;
}

expect(passFail(70)).toBe(true);

});