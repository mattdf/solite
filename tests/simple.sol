contract Test {
	address creator;
	address test = 1 + 2 + 3;

	function (int256) abc(int256 x, address y){
		while (x < y){
			x = x + y;
		}
		if (x > y){
			return x;
		}
		else if (x < y){
			return x + 1;
		}
		else if (x == y){
			return x + x;
		}
		else {
			return y;
		}
		return x+y;
	}

	function (uint256) def(){
		address a = 3;
		test = 1;
		return test;
	}
}
