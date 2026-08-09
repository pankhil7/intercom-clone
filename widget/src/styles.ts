export function injectStyles(primaryColor: string = '#4f46e5'): void {
  const style = document.createElement('style')
  style.id = 'inbox-widget-styles'
  style.textContent = `
    #inbox-widget-btn {
      position: fixed;
      bottom: 24px;
      right: 24px;
      width: 52px;
      height: 52px;
      border-radius: 50%;
      background: ${primaryColor};
      border: none;
      cursor: pointer;
      box-shadow: 0 4px 16px rgba(0,0,0,0.2);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 999998;
      transition: transform 0.2s, box-shadow 0.2s;
      outline: none;
    }
    #inbox-widget-btn:hover {
      transform: scale(1.05);
      box-shadow: 0 6px 20px rgba(0,0,0,0.25);
    }
    #inbox-widget-btn svg {
      width: 24px;
      height: 24px;
      fill: white;
    }
    #inbox-widget-badge {
      position: absolute;
      top: -2px;
      right: -2px;
      background: #ef4444;
      color: white;
      border-radius: 9999px;
      font-size: 10px;
      font-weight: 700;
      padding: 1px 5px;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      min-width: 16px;
      text-align: center;
      display: none;
    }
    #inbox-widget-panel {
      position: fixed;
      bottom: 88px;
      right: 24px;
      width: 360px;
      height: 520px;
      background: white;
      border-radius: 16px;
      box-shadow: 0 8px 40px rgba(0,0,0,0.18);
      display: flex;
      flex-direction: column;
      z-index: 999999;
      overflow: hidden;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      transform: scale(0.95) translateY(8px);
      opacity: 0;
      pointer-events: none;
      transition: transform 0.2s cubic-bezier(0.34,1.56,0.64,1), opacity 0.15s;
    }
    #inbox-widget-panel.open {
      transform: scale(1) translateY(0);
      opacity: 1;
      pointer-events: auto;
    }
    .iw-header {
      background: ${primaryColor};
      color: white;
      padding: 16px;
      flex-shrink: 0;
    }
    .iw-header h3 {
      margin: 0 0 2px;
      font-size: 15px;
      font-weight: 600;
    }
    .iw-header p {
      margin: 0;
      font-size: 12px;
      opacity: 0.85;
    }
    .iw-messages {
      flex: 1;
      overflow-y: auto;
      padding: 12px;
      display: flex;
      flex-direction: column;
      gap: 8px;
      scroll-behavior: smooth;
    }
    .iw-message {
      max-width: 80%;
      padding: 8px 12px;
      border-radius: 12px;
      font-size: 13px;
      line-height: 1.5;
      word-break: break-word;
    }
    .iw-message.contact {
      background: ${primaryColor};
      color: white;
      align-self: flex-end;
      border-bottom-right-radius: 4px;
    }
    .iw-message.agent {
      background: #f3f4f6;
      color: #111827;
      align-self: flex-start;
      border-bottom-left-radius: 4px;
    }
    .iw-message .iw-sender {
      font-size: 10px;
      font-weight: 600;
      margin-bottom: 2px;
      opacity: 0.7;
    }
    .iw-typing {
      display: none;
      align-self: flex-start;
      padding: 8px 12px;
      background: #f3f4f6;
      border-radius: 12px;
      border-bottom-left-radius: 4px;
      gap: 3px;
      align-items: center;
    }
    .iw-typing.visible { display: flex; }
    .iw-typing span {
      width: 6px;
      height: 6px;
      background: #9ca3af;
      border-radius: 50%;
      animation: iw-bounce 1s infinite;
    }
    .iw-typing span:nth-child(2) { animation-delay: 0.15s; }
    .iw-typing span:nth-child(3) { animation-delay: 0.3s; }
    @keyframes iw-bounce {
      0%, 60%, 100% { transform: translateY(0); }
      30% { transform: translateY(-4px); }
    }
    .iw-kb-results {
      margin: 0 12px;
      border: 1px solid #e5e7eb;
      border-radius: 8px;
      overflow: hidden;
      background: white;
      display: none;
    }
    .iw-input-area {
      padding: 10px 12px;
      border-top: 1px solid #f3f4f6;
      display: flex;
      gap: 8px;
      flex-shrink: 0;
      flex-direction: column;
    }
    .iw-input-row {
      display: flex;
      gap: 8px;
      align-items: flex-end;
    }
    .iw-input {
      flex: 1;
      border: 1px solid #e5e7eb;
      border-radius: 20px;
      padding: 8px 14px;
      font-size: 13px;
      outline: none;
      resize: none;
      max-height: 100px;
      font-family: inherit;
      line-height: 1.4;
    }
    .iw-input:focus {
      border-color: ${primaryColor};
      box-shadow: 0 0 0 2px ${primaryColor}20;
    }
    .iw-send-btn {
      width: 36px;
      height: 36px;
      border-radius: 50%;
      background: ${primaryColor};
      border: none;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
      transition: opacity 0.15s;
    }
    .iw-send-btn:disabled { opacity: 0.4; cursor: not-allowed; }
    .iw-send-btn svg { width: 16px; height: 16px; fill: white; }
    .iw-email-gate {
      padding: 20px;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }
    .iw-email-gate p {
      font-size: 13px;
      color: #374151;
      margin: 0;
    }
    .iw-email-gate input {
      border: 1px solid #e5e7eb;
      border-radius: 8px;
      padding: 8px 12px;
      font-size: 13px;
      width: 100%;
      box-sizing: border-box;
      outline: none;
      font-family: inherit;
    }
    .iw-email-gate input:focus {
      border-color: ${primaryColor};
    }
    .iw-email-gate button {
      background: ${primaryColor};
      color: white;
      border: none;
      border-radius: 8px;
      padding: 9px;
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      font-family: inherit;
    }
    .iw-empty {
      flex: 1;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      color: #9ca3af;
      font-size: 12px;
      gap: 8px;
    }
    @media (max-width: 400px) {
      #inbox-widget-panel {
        right: 0;
        bottom: 0;
        width: 100%;
        height: 100%;
        border-radius: 0;
      }
      #inbox-widget-btn {
        bottom: 16px;
        right: 16px;
      }
    }
  `
  document.head.appendChild(style)
}
