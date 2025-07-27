using UnityEngine;
using UnityEngine.UI;
using System.Collections;

public class ChatSystem : MonoBehaviour
{
    public InputField chatInputField; // �����
    public Text chatLog; // �����¼��ʾ����
    public Button sendButton; // ���Ͱ�ť����ѡ��
    public ScrollRect scrollRect; // �������򣨿�ѡ��
    public DeepSeekAPI deepSeekAPI;
    void Start()
    {
        // �������Ͱ�ť�ĵ���¼�
        if (sendButton != null)
        {
            sendButton.onClick.AddListener(SendMessageToChat);
        }

        // ���������Ļس����¼�
        chatInputField.onEndEdit.AddListener(OnInputEndEdit);
    }

    void OnInputEndEdit(string text)
    {
        // ����Ƿ����˻س���
        if (Input.GetKey(KeyCode.Return) || Input.GetKey(KeyCode.KeypadEnter))
        {
            SendMessageToChat();
        }
    }

    void SendMessageToChat()
    {
        chatInputField.interactable = false;
        // ��ȡ������е�����
        string message = chatInputField.text;

        // �����ϢΪ�գ��򲻷���
        if (string.IsNullOrWhiteSpace(message))
        {
            return;
        }
        
        deepSeekAPI.SendMessageToDeepSeek(message, (info) => { StartTypewriter(info + "\n" + "\n"); });
        // ��ʾ�û���Ϣ
        chatLog.text += "��: " + message + "\n"+"\n";

        // ��������
        chatInputField.text = "";

        // ���¼��������
        chatInputField.ActivateInputField();

        // ������������
        if (scrollRect != null)
        {
            Canvas.ForceUpdateCanvases();
            scrollRect.verticalNormalizedPosition = 0f;
        }

        // ģ��AI�ظ�
       
    }
   // public Text typewriterText; // ������ʾ����Ч����Text���
  
    private string fullText; // �������ı�����
    private bool isTyping = false; // �Ƿ����ڴ���
    // ��ʼ����Ч��
    public void StartTypewriter(string text)
    {
        if (isTyping)
        {
            // ������ڴ��֣���������ǰЧ��
            StopAllCoroutines();
         //   typewriterText.text = fullText;
            isTyping = false;
            return;
        }

        // ���������ı�
        fullText = text;
       // typewriterText.text = "";

        // ����Э��
        StartCoroutine(TypeText());
    }

    // ����Ч��Э��
    IEnumerator TypeText()
    {
        isTyping = true;
        string s = "";
        chatLog.text += "DeepSeek:";
        // ����ַ���ʾ�ı�
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