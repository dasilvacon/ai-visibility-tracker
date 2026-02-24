  import json                                                                   
                                                                                
  try:                                                                          
      with open('config/config.json', 'r') as f:                                
          config = json.load(f)                                                 
                                                                                
      print('✓ Config file loaded successfully')                                
                                                                                
      api_keys = config.get('api_keys', {})                                     
      configured_keys = [k for k in api_keys.keys() if not                      
  api_keys[k].startswith('YOUR_')]                                              
                                                                                
      print(f'✓ API keys configured: {", ".join(configured_keys)}')             
                                                                                
      print('\nPlatform status:')                                               
      for platform in ['openai', 'anthropic', 'perplexity', 'gemini']:          
          if platform in configured_keys:                                       
              print(f'  ✓ {platform.capitalize()}')                             
          else:                                                                 
              print(f'  ✗ {platform.capitalize()} (not configured)')            
                                                                                
  except FileNotFoundError:                                                     
      print('✗ config/config.json not found')                                   
      print('  Run: cp config/config.template.json config/config.json')         
  except json.JSONDecodeError:                                                  
      print('✗ config/config.json has invalid JSON')                            
  except Exception as e:                                                        
      print(f'✗ Error: {e}')                                                    
  EOF   


