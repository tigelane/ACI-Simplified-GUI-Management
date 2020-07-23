# Testing Docs

* Use `pytest` to run tests
* Use `pytest -vv` to run tests verbosely
* Pytest-cov is installed, use `pytest --cov=pge_aci_web  --cov-report=term-missing` to get coverage report on missing lines
* Use `pytest --cov=pge_aci_web --cov=SourceControlMgmt --cov-report=term-missing` to get coverage report on multiple files

## Example of pytest coverage report
```
============================================================================================================ 36 passed in 2.15s =============================================================================================================
root@38a3bc1d8483:/workspaces/pge-aci-automation/pge-aci-web# pytest --cov=pge_aci_web  --cov-report=term-missing
============================================================================================================ test session starts ============================================================================================================
platform linux -- Python 3.6.8, pytest-5.2.1, py-1.8.0, pluggy-0.13.0
rootdir: /workspaces/pge-aci-automation/pge-aci-web, inifile: pytest.ini
plugins: cov-2.8.1, mock-1.11.1
collected 36 items                                                                                                                                                                                                                          

tests/test_pge_aci_web.py ....................................                                                                                                                                                                        [100%]

----------- coverage: platform linux, python 3.6.8-final-0 -----------
Name             Stmts   Miss  Cover   Missing
----------------------------------------------
pge_aci_web.py     373    160    57%   80-92, 98-102, 125, 149-162, 168, 226-235, 246-280, 289-298, 310-317, 327-360, 435, 440, 445, 453, 455, 457, 459, 602-605, 613-614, 618, 624-647, 651-676, 685-687, 695, 700-704


============================================================================================================ 36 passed in 1.91s =============================================================================================================
```