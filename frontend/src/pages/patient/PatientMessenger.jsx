import { useSearchParams } from 'react-router-dom';
import ChatWindow from '../../components/ChatWindow';
import PatientLayout from './PatientLayout';
import '../../styles/messenger.css';

export default function PatientMessenger() {
  const [searchParams] = useSearchParams();
  const initialConversationId = searchParams.get('conversationId') || '';

  return (
    <PatientLayout>
      <div className="page-header">
        <div>
          <h1>Doctor-Patient Messenger</h1>
          <p>Communicate directly in real time with your consulting ophthalmologist.</p>
        </div>
      </div>
      <ChatWindow initialConversationId={initialConversationId} />
    </PatientLayout>
  );
}
