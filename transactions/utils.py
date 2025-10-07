def mask_email(email):
    """
    Mask email address for display in transaction tables.
    Example: 'abcdef@gmail.com' -> 'abc***@gm...om'
    """
    if not email or '@' not in email:
        return email
    
    local_part, domain = email.split('@')
    
    # Mask local part - show first 3 characters
    if len(local_part) > 3:
        masked_local = local_part[:3] + '***'
    else:
        masked_local = local_part + '***'
    
    # Mask domain - show first 2 and last 2 characters
    domain_parts = domain.split('.')
    if len(domain_parts) >= 2:
        main_domain = '.'.join(domain_parts[:-1])
        tld = domain_parts[-1]
        
        if len(main_domain) > 2:
            masked_domain = main_domain[:2] + '...' + main_domain[-1:] if len(main_domain) > 3 else main_domain
        else:
            masked_domain = main_domain
            
        masked_domain += '.' + tld
    else:
        masked_domain = domain[:2] + '...' + domain[-2:] if len(domain) > 4 else domain
    
    return f"{masked_local}@{masked_domain}"

def to_display_currency(amount, currency, currency_rate=1):
    """
    Convert amount to display currency using currency rate.
    """
    if currency.upper() == 'USD':
        return amount * currency_rate
    return amount