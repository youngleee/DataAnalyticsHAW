# Virtual Environment Activation Guide

## Quick Activation

### Windows (PowerShell or Command Prompt)
```bash
venv\Scripts\activate
```

### Windows (Git Bash)
```bash
source venv/Scripts/activate
```

### Linux/Mac
```bash
source venv/bin/activate
```

## Verification

After activation, you should see `(venv)` at the beginning of your terminal prompt:
```
(venv) C:\Users\young\DataAnalyticsHAW\DataAnalyticsHAW>
```

## Deactivation

To deactivate the virtual environment:
```bash
deactivate
```

## Installing Dependencies

After activating the virtual environment, install project dependencies:
```bash
pip install -r requirements.txt
```

## Troubleshooting

### Issue: "venv\Scripts\activate : The term 'activate' is not recognized"
**Solution**: Make sure you're in the project root directory and the venv folder exists. Try:
```bash
.\venv\Scripts\activate
```

### Issue: "python: command not found" (Linux/Mac)
**Solution**: Use `python3`:
```bash
python3 -m venv venv
source venv/bin/activate
```

### Issue: Permission denied (Linux/Mac)
**Solution**: Make the activation script executable:
```bash
chmod +x venv/bin/activate
```

