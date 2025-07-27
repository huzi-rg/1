using UnityEngine;
using UnityEngine.UI;
using System.Collections;

public class ChatSystem : MonoBehaviour
{
    public InputField chatInputField; // 输入框
    public Text chatLog; // 聊天记录显示区域
    public Button sendButton; // 发送按钮（可选）
    public ScrollRect scrollRect; // 滚动区域（可选）
    public DeepSeekAPI deepSeekAPI;
    void Start()
    {
        // 监听发送按钮的点击事件
        if (sendButton != null)
        {
            sendButton.onClick.AddListener(SendMessageToChat);
        }

        // 监听输入框的回车键事件
        chatInputField.onEndEdit.AddListener(OnInputEndEdit);
    }

    void OnInputEndEdit(string text)
    {
        // 检查是否按下了回车键
        if (Input.GetKey(KeyCode.Return) || Input.GetKey(KeyCode.KeypadEnter))
        {
            SendMessageToChat();
        }
    }

    void SendMessageToChat()
    {
        chatInputField.interactable = false;
        // 获取输入框中的文字
        string message = chatInputField.text;

        // 如果消息为空，则不发送
        if (string.IsNullOrWhiteSpace(message))
        {
            return;
        }
        
        deepSeekAPI.SendMessageToDeepSeek(message, (info) => { StartTypewriter(info + "\n" + "\n"); });
        // 显示用户消息
        chatLog.text += "我: " + message + "\n"+"\n";

        // 清空输入框
        chatInputField.text = "";

        // 重新激活输入框
        chatInputField.ActivateInputField();

        // 调整滚动区域
        if (scrollRect != null)
        {
            Canvas.ForceUpdateCanvases();
            scrollRect.verticalNormalizedPosition = 0f;
        }

        // 模拟AI回复
       
    }
   // public Text typewriterText; // 用于显示打字效果的Text组件
  
    private string fullText; // 完整的文本内容
    private bool isTyping = false; // 是否正在打字
    // 开始打字效果
    public void StartTypewriter(string text)
    {
        if (isTyping)
        {
            // 如果正在打字，则跳过当前效果
            StopAllCoroutines();
         //   typewriterText.text = fullText;
            isTyping = false;
            return;
        }

        // 设置完整文本
        fullText = text;
       // typewriterText.text = "";

        // 启动协程
        StartCoroutine(TypeText());
    }

    // 打字效果协程
    IEnumerator TypeText()
    {
        isTyping = true;
        string s = "";
        chatLog.text += "DeepSeek:";
        // 逐个字符显示文本
        for (int i = 0; i < fullText.Length; i++)
        {
          //  s = fullText.Substring(0, i);
            chatLog.text += fullText[i];
           
            yield return 1;
        }
        chatInputField.interactable = true;
        scrollRect.verticalNormalizedPosition = 0f;
        chatInputField.ActivateInputField();
        isTyping = false;
    }
}